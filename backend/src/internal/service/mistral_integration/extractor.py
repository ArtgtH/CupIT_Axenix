"""
Модуль для извлечения сущностей из текста пользователя.
"""

import re
import logging
from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime

from .entities import TravelEntities
from .api_client import MistralAIClient, APIError


logger = logging.getLogger(__name__)


class EntityExtractor:
    """
    Класс для извлечения сущностей путешествия из текста пользователя.
    Использует Mistral AI API для извлечения, и имеет резервные алгоритмы
    для случаев, когда API недоступно.
    """
    
    def __init__(self, api_client: Optional[MistralAIClient] = None):
        """
        Инициализирует экстрактор сущностей.
        
        Args:
            api_client: Клиент для работы с Mistral AI API
        """
        self.api_client = api_client or MistralAIClient()
        
    def extract_entities(self, message: str, current_entities: TravelEntities) -> TravelEntities:
        """
        Извлекает сущности из сообщения пользователя.
        Сначала пытается использовать Mistral AI API, при неудаче
        использует резервные алгоритмы.
        
        Args:
            message: Текст сообщения пользователя
            current_entities: Текущие извлеченные сущности
            
        Returns:
            Обновленные сущности
        """
        try:
            # Пытаемся использовать Mistral AI API
            extracted_dict = self.api_client.extract_entities(message, current_entities.to_dict())
            
            # Создаем новый объект сущностей
            new_entities = TravelEntities()
            
            # Обновляем существующие значения новыми
            for key, value in current_entities.to_dict().items():
                if key in extracted_dict:
                    # Для prefered_transport объединяем значения
                    if key == "prefered_transport":
                        new_pref = {**value, **extracted_dict[key]}
                        setattr(new_entities, key, new_pref)
                    else:
                        if extracted_dict[key] or not value:
                            setattr(new_entities, key, extracted_dict[key])
                        else:
                            setattr(new_entities, key, value)
                else:
                    setattr(new_entities, key, value)

            logger.info(f"Сущности извлечены с помощью Mistral AI: {new_entities.to_dict()}")
            return new_entities

        except APIError as e:
            logger.warning(f"Ошибка при извлечении сущностей с помощью Mistral AI: {e}. "
                          f"Использую резервные алгоритмы.")
            return self._extract_entities_fallback(message, current_entities)

    def _extract_entities_fallback(self, message: str, current_entities: TravelEntities) -> TravelEntities:
        """
        Резервный метод извлечения сущностей с использованием регулярных выражений.
        """
        extracted = current_entities.to_dict()

        # Извлечение даты
        if not extracted["date"]:
            extracted["date"] = self._extract_date(message)

        # Извлечение городов
        cities = self._extract_cities(message)

        if cities["start_city"] and not extracted["start_city"]:
            extracted["start_city"] = cities["start_city"]

        if cities["end_city"] and not extracted["end_city"]:
            extracted["end_city"] = cities["end_city"]

        if cities["mid_city"]:
            mid_cities = set(extracted["mid_city"])
            mid_cities.update(cities["mid_city"])
            extracted["mid_city"] = list(mid_cities)

        # Извлечение транспорта
        extracted["prefered_transport"] = self._extract_transport(
            message,
            extracted["prefered_transport"]
        )

        logger.info(f"Сущности извлечены с помощью резервных алгоритмов: {extracted}")
        return TravelEntities(extracted)

    def _extract_transport(self, message: str, current_transport: Dict[str, int]) -> Dict[str, int]:
        """
        Извлекает предпочитаемый транспорт из сообщения.

        Args:
            message: Текст сообщения
            current_transport: Текущие настройки транспорта

        Returns:
            Обновленный словарь с предпочтениями
        """
        transport = current_transport.copy()
        keywords = {
            "train": ["поезд", "жд", "рельсы", "вагон"],
            "plane": ["самолет", "авиа", "полет", "аэропорт"],
            "bus": ["автобус", "автовокзал", "рейс"]
        }

        msg_lower = message.lower()
        for transport_type, keys in keywords.items():
            if any(key in msg_lower for key in keys):
                transport[transport_type] = 1

        return transport

    def _extract_date(self, message: str) -> str:
        """
        Извлекает дату из сообщения.

        Args:
            message: Текст сообщения пользователя

        Returns:
            Дата в формате dd.mm.yyyy или пустая строка
        """
        # Ищем дату в формате дд.мм.гггг, дд/мм/гггг, дд-мм-гггг
        date_pattern = r'(\d{1,2}[./-]\d{1,2}[./-]\d{2,4})'
        date_match = re.search(date_pattern, message)

        if not date_match:
            # Ищем текстовые упоминания даты
            date_words = {
                'сегодня': datetime.now(),
                'завтра': datetime.now().replace(day=datetime.now().day + 1),
                'послезавтра': datetime.now().replace(day=datetime.now().day + 2)
            }

            for word, date_obj in date_words.items():
                if word in message.lower():
                    return date_obj.strftime("%d.%m.%Y")

            return ""

        date_str = date_match.group(1)
        # Преобразование в формат dd.mm.yyyy если возможно
        try:
            if '/' in date_str:
                day, month, year = date_str.split('/')
            elif '-' in date_str:
                day, month, year = date_str.split('-')
            else:
                day, month, year = date_str.split('.')

            # Проверка на корректность порядка (день/месяц/год)
            if len(day) == 4:  # Если первое число - год, то порядок год-месяц-день
                year, month, day = day, month, year

            if len(year) == 2:
                year = '20' + year

            # Валидация значений даты
            day_int, month_int, year_int = int(day), int(month), int(year)
            if not (1 <= day_int <= 31 and 1 <= month_int <= 12 and 2000 <= year_int <= 2100):
                return ""

            return f"{day_int:02d}.{month_int:02d}.{year}"
        except Exception as e:
            logger.error(f"Ошибка при парсинге даты: {e}")
            return ""

    def _extract_cities(self, message: str) -> Dict[str, Any]:
        """
        Извлекает города из сообщения.

        Args:
            message: Текст сообщения пользователя

        Returns:
            Словарь с извлеченными городами
        """
        result = {
            "start_city": "",
            "end_city": "",
            "mid_city": []
        }

        # Словарь ключевых слов для разных типов городов
        city_keywords = {
            "start_city": ["из", "от", "откуда", "отправление из", "выезжаю из", "старт из"],
            "end_city": ["в", "до", "куда", "прибытие в", "приезжаю в", "конечная точка", "финиш в"],
            "mid_city": ["через", "с остановкой в", "проезжая", "заезжая в", "с заездом в"]
        }

        # Шаблон для извлечения городских названий (города с большой буквы)
        city_pattern = r'(?:^|\s)([А-Я][а-яА-ЯёЁ-]+)(?:$|\s|,|\.|!|\?)'

        # Поиск городов с использованием ключевых слов
        for entity_type, keywords in city_keywords.items():
            for keyword in keywords:
                pattern = f"{keyword}\\s+([А-Я][а-яА-ЯёЁ-]+)"
                for match in re.finditer(pattern, message, re.IGNORECASE):
                    city = match.group(1).strip()
                    if entity_type == "mid_city":
                        if city not in result["mid_city"]:
                            result["mid_city"].append(city)
                    elif not result[entity_type]:
                        result[entity_type] = city

        # Если города все еще не найдены, используем контекстный анализ
        if not (result["start_city"] and result["end_city"]) and "из" in message and "в" in message:
            # Ищем шаблон "из [город] в [город]"
            iz_v_pattern = r'из\s+([А-Я][а-яА-ЯёЁ-]+)\s+в\s+([А-Я][а-яА-ЯёЁ-]+)'
            iz_v_match = re.search(iz_v_pattern, message, re.IGNORECASE)

            if iz_v_match:
                if not result["start_city"]:
                    result["start_city"] = iz_v_match.group(1)
                if not result["end_city"]:
                    result["end_city"] = iz_v_match.group(2)

        # Если города все еще не определены, ищем первые два города в тексте
        if not (result["start_city"] and result["end_city"]):
            cities = []
            for match in re.finditer(city_pattern, message):
                city = match.group(1)
                if city not in cities:
                    cities.append(city)

            if len(cities) >= 2 and not result["start_city"] and not result["end_city"]:
                result["start_city"] = cities[0]
                result["end_city"] = cities[-1]
                if len(cities) > 2:
                    result["mid_city"].extend(cities[1:-1])

        return result