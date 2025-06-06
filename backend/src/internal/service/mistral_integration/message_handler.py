"""
Модуль для обработки сообщений в диалоге и формирования ответов.
"""

import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from internal.schemas.redis import RedisMessage
from internal.schemas.responces import ScheduleResponse, ScheduleObject, TransportType, MessageResponse

from .entities import TravelEntities
from .extractor import EntityExtractor
from internal.service.get_routes import get_routes

logger = logging.getLogger(__name__)


class MessageHandler:
    """
    Класс для обработки сообщений пользователя и формирования ответов.
    Отвечает за извлечение сущностей из истории сообщений и формирование ответов.
    """
    
    _instance = None
    
    @classmethod
    def get_instance(cls, entity_extractor: Optional[EntityExtractor] = None):
        """
        Получает синглтон-экземпляр MessageHandler.
        
        Args:
            entity_extractor: Экстрактор сущностей
            
        Returns:
            Экземпляр MessageHandler
        """
        if cls._instance is None:
            cls._instance = cls(entity_extractor)
        return cls._instance
    
    @classmethod
    def reset_instance(cls):
        """
        Сбрасывает синглтон-экземпляр MessageHandler.
        """
        cls._instance = None
    
    def __init__(self, entity_extractor: Optional[EntityExtractor] = None):
        """
        Инициализирует обработчик сообщений.
        
        Args:
            entity_extractor: Экстрактор сущностей
        """
        self.entity_extractor = entity_extractor or EntityExtractor()
    
    def process_message(self, thread: List[RedisMessage]) -> ScheduleResponse | MessageResponse:
        """
        Обрабатывает входящее сообщение и историю сообщений пользователя, формирует ответ.
        
        Args:
            thread: История сообщений, включая текущее сообщение пользователя
            
        Returns:
            ScheduleResponse, если все сущности извлечены
            MessageResponse, если требуется дополнительная информация
        """
        if not thread:
            return MessageResponse(text="Пожалуйста, введите сообщение для обработки.")
        
        # Извлекаем текст текущего сообщения (последнее в списке)
        current_message = self._get_message_text(thread[-1])
        
        # Извлекаем сущности из всей истории сообщений
        entities = self._extract_entities_from_thread(thread)
        
        # Проверяем, все ли необходимые сущности извлечены
        if entities.is_complete():
            # Все сущности извлечены, можно возвращать расписание
            return self._generate_schedule_response(entities)
        else:
            # Требуется уточнение
            response_text = self._generate_clarification_message(entities)
            return MessageResponse(text=response_text)
    
    def _get_message_text(self, message: RedisMessage) -> str:
        """
        Извлекает текст из сообщения.
        
        Args:
            message: Сообщение
            
        Returns:
            Текст сообщения
        """
        try:
            if isinstance(message, bytes):
                message_dict = json.loads(message.decode('utf-8'))
                return message_dict.get('text', '')
            elif hasattr(message, 'text'):
                # Пробуем проверить, является ли text JSON строкой
                try:
                    message_dict = json.loads(message.text)
                    return message_dict.get('text', message.text)
                except json.JSONDecodeError:
                    # Если не JSON, возвращаем как есть
                    return message.text
            else:
                # Если ничего не подходит, пробуем преобразовать к строке
                return str(message)
        except Exception as e:
            logger.error(f"Ошибка при извлечении текста из сообщения: {e}")
            return ""
    
    def _extract_entities_from_thread(self, thread: List[RedisMessage]) -> TravelEntities:
        """
        Извлекает сущности из всей истории сообщений.
        
        Args:
            thread: История сообщений
            
        Returns:
            Извлеченные сущности
        """
        entities = TravelEntities()
        
        # Объединяем текст всех сообщений в один
        full_dialogue = " ".join(self._get_message_text(message) for message in thread if self._get_message_text(message))
        
        # Извлекаем сущности из полного текста диалога
        entities = self.entity_extractor.extract_entities(full_dialogue, entities)
        
        return entities
    
    def _generate_clarification_message(self, entities: TravelEntities) -> str:
        """
        Формирует уточняющее сообщение на основе извлеченных и отсутствующих сущностей.
        
        Args:
            entities: Извлеченные сущности
            
        Returns:
            Текст уточняющего сообщения
        """
        missing = entities.get_missing_entities()
        
        # Если все сущности извлечены (это проверка на всякий случай)
        if not missing:
            route = entities.get_route_description()
            return f"Отлично! Я подобрал для вас маршрут: {route} на {entities.date}. Вот доступные варианты транспорта:"
        
        # Формирование уточняющего вопроса в зависимости от того, что отсутствует
        if len(missing) == 3:
            # Ничего не извлечено
            return ("Добрый день! Чтобы подобрать для вас оптимальный маршрут, мне нужна информация о поездке. "
                   "Пожалуйста, укажите дату поездки, город отправления и город прибытия.")
        
        message_parts = []
        
        if "date" in missing:
            message_parts.append("дату поездки")
        
        if "start_city" in missing:
            message_parts.append("город отправления")
        
        if "end_city" in missing:
            message_parts.append("город прибытия")
        
        # Добавляем уточнение по предпочитаемому транспорту, если он не указан
        if not any(entities.prefered_transport.values()):
            message_parts.append("предпочитаемый транспорт (поезд, самолет, автобус)")

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

        # Добавляем информацию о предпочитаемом транспорте, если она есть
        if any(entities.prefered_transport.values()):
            transport_preferences = []
            if entities.prefered_transport["train"]:
                transport_preferences.append("поезд")
            if entities.prefered_transport["plane"]:
                transport_preferences.append("самолет")
            if entities.prefered_transport["bus"]:
                transport_preferences.append("автобус")
            if transport_preferences:
                known_parts.append(f"предпочитаемый транспорт: {', '.join(transport_preferences)}")

        if known_parts:
            message += f"\n\nУже указано: {'; '.join(known_parts)}."

        return message

    def _generate_schedule_response(self, entities: TravelEntities) -> ScheduleResponse:
        """
        Формирует ответ с расписанием на основе извлеченных сущностей.
        Использует API маршрутов для получения реальных данных.

        Args:
            entities: Извлеченные сущности

        Returns:
            Ответ с расписанием
        """
        # Преобразуем дату в нужный формат (из dd.mm.yyyy в yyyy-mm-dd)
        try:
            date_parts = entities.date.split('.')
            api_date_format = f"{date_parts[2]}-{date_parts[1]}-{date_parts[0]}"
        except (IndexError, ValueError, AttributeError) as e:
            logger.error(f"Ошибка при преобразовании даты {entities.date}: {e}")
            # Используем текущую дату при ошибке
            api_date_format = datetime.now().strftime("%Y-%m-%d")

        if entities.mid_city:
            stops = [entities.start_city] + entities.mid_city + [entities.end_city]
        else:
            stops = [entities.start_city, entities.end_city]

        # Получаем маршруты с учетом предпочитаемого транспорта
        schedule_response = get_routes(stops, api_date_format, entities.prefered_transport)
        
        if schedule_response is None:
            return MessageResponse(text="Не удалось получить данные о маршруте. Попробуйте уточнить ваш запрос.")

        return schedule_response