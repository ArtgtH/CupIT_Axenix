"""
Модуль для обработки сообщений в диалоге и формирования ответов.
"""

import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from internal.schemas.redis import RedisMessage
from internal.schemas.responces import ScheduleResponse, ScheduleObject, TransportType, MessageResponse

from .entities import TravelEntities
from .extractor import EntityExtractor


logger = logging.getLogger(__name__)


class MessageHandler:
    """
    Класс для обработки сообщений пользователя и формирования ответов.
    Отвечает за сохранение контекста, формирование ответов и принятие решений
    о готовности извлеченных данных.
    """
    
    def __init__(self, entity_extractor: Optional[EntityExtractor] = None):
        """
        Инициализирует обработчик сообщений.
        
        Args:
            entity_extractor: Экстрактор сущностей
        """
        self.entity_extractor = entity_extractor or EntityExtractor()
    
    def process_message(self, input_text: str, message_history: List[RedisMessage]) -> ScheduleResponse | MessageResponse:
        """
        Обрабатывает входящее сообщение от пользователя и формирует ответ.
        
        Args:
            input_text: Текст сообщения пользователя
            message_history: История сообщений
            
        Returns:
            ScheduleResponse, если все сущности извлечены
            MessageResponse, если требуется дополнительная информация
        """
        # Извлекаем текущие сущности из истории сообщений
        current_entities = self._parse_message_history(message_history)
        
        # Извлекаем новые сущности из входного сообщения
        updated_entities = self.entity_extractor.extract_entities(input_text, current_entities)
        
        # Проверяем, все ли необходимые сущности извлечены
        if updated_entities.is_complete():
            # Все сущности извлечены, можно возвращать расписание
            return self._generate_schedule_response(updated_entities)
        else:
            # Требуется уточнение
            response_text = self._generate_clarification_message(updated_entities)
            return MessageResponse(text=response_text)
    
    def _parse_message_history(self, messages: List[RedisMessage]) -> TravelEntities:
        """
        Извлекает текущие сущности из истории сообщений.
        
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
            elif hasattr(first_message, 'text'):
                try:
                    entities_dict = json.loads(first_message.text)
                    return TravelEntities(entities_dict)
                except (json.JSONDecodeError, AttributeError):
                    pass
        except (json.JSONDecodeError, IndexError, UnicodeDecodeError, AttributeError) as e:
            logger.error(f"Ошибка при парсинге истории сообщений: {e}")
        
        return TravelEntities()
    
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
    
    def _generate_schedule_response(self, entities: TravelEntities) -> ScheduleResponse:
        """
        Формирует ответ с расписанием на основе извлеченных сущностей.
        
        Args:
            entities: Извлеченные сущности
            
        Returns:
            Ответ с расписанием
        """
        # Здесь в реальном приложении был бы запрос в сервис расписаний
        # В этом примере просто возвращаем тестовые данные
        
        current_timestamp = int(datetime.now().timestamp())
        
        # Формируем объекты расписания с разными типами транспорта
        schedule_objects = [
            ScheduleObject(
                type=TransportType.bus,
                time_start_utc=current_timestamp,
                time_end_utc=current_timestamp + 3600,  # +1 час
                place_start=entities.start_city,
                place_finish=entities.end_city,
                ticket_url="http://example.com/ticket/bus",
            ),
            ScheduleObject(
                type=TransportType.train,
                time_start_utc=current_timestamp + 1800,  # +30 минут от текущего времени
                time_end_utc=current_timestamp + 5400,  # +1.5 часа от текущего времени
                place_start=entities.start_city,
                place_finish=entities.end_city,
                ticket_url="http://example.com/ticket/train",
            )
        ]
        
        # Добавляем самолет если есть промежуточные города
        if entities.mid_city:
            schedule_objects.append(
                ScheduleObject(
                    type=TransportType.plane,
                    time_start_utc=current_timestamp + 3600,  # +1 час от текущего времени
                    time_end_utc=current_timestamp + 7200,  # +2 часа от текущего времени
                    place_start=entities.start_city,
                    place_finish=entities.end_city,
                    ticket_url="http://example.com/ticket/plane",
                )
            )
        
        return ScheduleResponse(objects=schedule_objects) 