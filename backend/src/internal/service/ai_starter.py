from typing import List, Dict, Any, Optional
import json
import re
import requests
from datetime import datetime
import os

from internal.schemas.redis import RedisMessage, ThreadStatus
from internal.schemas.responces import (
    ScheduleResponse,
    ScheduleObject,
    TransportType,
    MessageResponse,
)

from internal.service.mistral_integration.message_handler import MessageHandler


class TravelEntities:
	"""Класс для хранения и управления извлеченными сущностями путешествия."""
	
	def __init__(self, data: Optional[Dict[str, Any]] = None):
		self.date: str = data.get("date", "") if data else ""
		self.start_city: str = data.get("start_city", "") if data else ""
		self.end_city: str = data.get("end_city", "") if data else ""
		self.mid_city: List[str] = data.get("mid_city", []) if data else []
	
	def to_dict(self) -> Dict[str, Any]:
		return {
			"date": self.date,
			"start_city": self.start_city,
			"end_city": self.end_city,
			"mid_city": self.mid_city
		}
	
	def is_complete(self) -> bool:
		"""Проверяет, все ли необходимые сущности извлечены."""
		return bool(self.date and self.start_city and self.end_city)
	
	def get_missing_entities(self) -> List[str]:
		"""Возвращает список отсутствующих сущностей."""
		missing = []
		if not self.date:
			missing.append("date")
		if not self.start_city:
			missing.append("start_city")
		if not self.end_city:
			missing.append("end_city")
		return missing


def extract_entities_from_message(message: str, current_entities: TravelEntities) -> TravelEntities:
	"""
	Извлекает сущности из сообщения пользователя, используя Mistral AI API.
	
	Args:
		message: Текст сообщения пользователя
		current_entities: Текущие извлеченные сущности
		
	Returns:
		Обновленные сущности
	"""
	# Формируем промпт для Mistral AI
	prompt = f"""
	Извлеки следующие сущности из текста пользователя и верни их в формате JSON:
	
	- date: Дата в формате dd.mm.yyyy
	- start_city: Город отправления на русском языке
	- end_city: Город прибытия на русском языке
	- mid_city: Список промежуточных городов на русском языке (может быть пустым)
	
	Текущие извлеченные сущности:
	{json.dumps(current_entities.to_dict(), ensure_ascii=False)}
	
	Текст пользователя:
	{message}
	
	Верни только JSON, без дополнительного текста. Если какая-то сущность не найдена, оставь существующее значение или пустую строку.
	"""
	
	# Вызов Mistral AI API
	response = requests.post(
		"https://api.mistral.ai/v1/chat/completions",
		headers={
			"Authorization": f"Bearer {os.getenv('MISTRAL_API_KEY', '')}",
			"Content-Type": "application/json"
		},
		json={
			"model": "mistral-large-latest",
			"messages": [{"role": "user", "content": prompt}],
			"temperature": 0.1,
			"max_tokens": 500
		}
	)
	
	extracted = current_entities.to_dict()
	
	try:
		result = response.json()
		content = result["choices"][0]["message"]["content"]
		extracted_data = json.loads(content)
		
		# Обновляем только те поля, которые были извлечены
		for key, value in extracted_data.items():
			if value and key in extracted:
				extracted[key] = value
	except Exception as e:
		print(f"Ошибка при обработке ответа Mistral AI: {e}")
	
	return TravelEntities(extracted)


def get_response_message(entities: TravelEntities) -> str:
	"""
	Формирует ответное сообщение на основе извлеченных и отсутствующих сущностей.
	
	Args:
		entities: Извлеченные сущности
		
	Returns:
		Текст ответного сообщения
	"""
	missing = entities.get_missing_entities()
	
	if not missing:
		# Все сущности извлечены
		cities = [entities.start_city]
		if entities.mid_city:
			cities.extend(entities.mid_city)
		cities.append(entities.end_city)
		
		route = " → ".join(cities)
		return f"Отлично! Я подобрал для вас маршрут: {route} на {entities.date}. Вот доступные варианты транспорта:"
	
	# Формирование уточняющего вопроса
	if len(missing) == 3:
		# Ничего не извлечено
		return "Пожалуйста, укажите дату поездки, город отправления и город прибытия."
	
	message_parts = []
	
	if "date" in missing:
		message_parts.append("дату поездки")
	
	if "start_city" in missing:
		message_parts.append("город отправления")
	
	if "end_city" in missing:
		message_parts.append("город прибытия")
	
	message = "Пожалуйста, укажите " + ", ".join(message_parts) + "."
	
	# Если что-то уже извлечено, добавим это в сообщение
	known_parts = []
	
	if entities.date:
		known_parts.append(f"дата: {entities.date}")
	
	if entities.start_city:
		known_parts.append(f"откуда: {entities.start_city}")
	
	if entities.end_city:
		known_parts.append(f"куда: {entities.end_city}")
	
	if entities.mid_city:
		mid_cities = ", ".join(entities.mid_city)
		known_parts.append(f"через: {mid_cities}")
	
	if known_parts:
		message += f"\n\nУже указано: {'; '.join(known_parts)}."
	
	return message


def parse_message_history(messages: List[RedisMessage]) -> TravelEntities:
	"""
	Извлекает текущие сущности из первого сообщения в истории.
	
	Args:
		messages: История сообщений
		
	Returns:
		Извлеченные сущности
	"""
	if not messages:
		return TravelEntities()
	
	try:
		# Первое сообщение содержит текущее состояние сущностей
		first_message = messages[0]
		if isinstance(first_message, bytes):
			entities_dict = json.loads(first_message.decode('utf-8'))
			return TravelEntities(entities_dict)
		elif isinstance(first_message, RedisMessage):
			entities_dict = json.loads(first_message.text)
			return TravelEntities(entities_dict)
	except (json.JSONDecodeError, IndexError, UnicodeDecodeError, AttributeError):
		pass
	
	return TravelEntities()


def talk_with_god(
    input_text: str, thread: List[ThreadStatus | RedisMessage]
) -> ScheduleResponse | MessageResponse:
    """
    Функция для общения с пользователем и извлечения сущностей о маршруте.
    Использует Mistral AI API для извлечения сущностей из диалога.
    
    Args:
        input_text: Текст запроса пользователя
        thread: История сообщений
        
    Returns:
        ScheduleResponse, если все сущности извлечены
        MessageResponse, если требуется уточнение
    """
    # Создаем обработчик сообщений
    handler = MessageHandler()
    
    # Обрабатываем сообщение и получаем ответ
    return handler.process_message(input_text, thread)
