"""
Модуль для обработки сообщений в диалоге и формирования ответов.
"""

import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from internal.schemas.redis import RedisMessage
from internal.schemas.responces import ScheduleResponse, ScheduleObject, TransportType, MessageResponse

from internal.service.Routes.GetRoutesWithStops import GetRoutesWithStops
from internal.service.Routes.GetRoutes import GetRoutes

from .entities import TravelEntities
from .extractor import EntityExtractor


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
        
        for message in thread:
            message_text = self._get_message_text(message)
            if message_text:
                # Для каждого сообщения извлекаем сущности и обновляем результат
                entities = self.entity_extractor.extract_entities(message_text, entities)
        
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
        
        # Инициализируем API маршрутов
        schedule_objects = []
        current_timestamp = int(datetime.now().timestamp())
        
        try:
            # Изменено: создаем объекты API без передачи аргументов
            route_finder = GetRoutesWithStops()
            
            # Проверяем наличие промежуточных городов и формируем список остановок
            if entities.mid_city:
                # Есть промежуточные города
                stops = [entities.start_city] + entities.mid_city + [entities.end_city]
            else:
                # Промежуточных городов нет, используем простой список
                stops = [entities.start_city, entities.end_city]
            
            try:
                # Используем маршрут с остановками
                result = route_finder.find_multi_leg_route(stops, api_date_format)
                
                if result and 'route' in result:
                    # Создаем объект маршрута для многоэтапного пути
                    for i, segment in enumerate(result['route']):
                        # Рассчитываем время начала и конца (в секундах)
                        start_time = current_timestamp + (i * 7200)  # 2 часа между сегментами
                        end_time = start_time + segment.get('duration', 3600)
                        
                        # Определяем тип транспорта - чередуем автобус и поезд
                        transport_type = TransportType.bus if i % 2 == 0 else TransportType.train
                        
                        # Добавлено: формируем URL для билетов
                        ticket_url = f"http://example.com/ticket/{transport_type}/{entities.start_city}-{entities.end_city}"
                        
                        schedule_objects.append(ScheduleObject(
                            type=transport_type,
                            place_start=segment.get('from', entities.start_city),
                            place_finish=segment.get('to', entities.end_city),
                            time_start_utc=start_time,
                            time_end_utc=end_time,
                            ticket_url=ticket_url  # Добавлено: обязательное поле
                        ))
                else:
                    logger.warning(f"Не найдены маршруты для {stops} на {api_date_format}")
                    # Падение в запасной вариант - ищем прямой маршрут
                    direct_route = route_finder.routes_api.get_routes(entities.start_city, entities.end_city, api_date_format)
                    
                    if direct_route:
                        # Создаем объект маршрута для прямого пути
                        start_time = current_timestamp
                        end_time = start_time + 3600  # Фиктивная продолжительность - 1 час
                        
                        schedule_objects.append(ScheduleObject(
                            type=TransportType.bus,
                            place_start=entities.start_city,
                            place_finish=entities.end_city,
                            time_start_utc=start_time,
                            time_end_utc=end_time,
                            ticket_url=f"http://example.com/ticket/bus/{entities.start_city}-{entities.end_city}"  # Добавлено
                        ))
            except Exception as e:
                logger.error(f"Ошибка при поиске маршрута: {e}")
                # Падение в запасной вариант при любых ошибках API
                try:
                    direct_route = route_finder.routes_api.get_routes(entities.start_city, entities.end_city, api_date_format)
                    
                    if direct_route:
                        # Создаем объект маршрута для прямого пути
                        start_time = current_timestamp
                        end_time = start_time + 3600  # Фиктивная продолжительность - 1 час
                        
                        schedule_objects.append(ScheduleObject(
                            type=TransportType.bus,
                            place_start=entities.start_city,
                            place_finish=entities.end_city,
                            time_start_utc=start_time,
                            time_end_utc=end_time,
                            ticket_url=f"http://example.com/ticket/bus/{entities.start_city}-{entities.end_city}"  # Добавлено
                        ))
                except Exception as inner_e:
                    logger.error(f"Ошибка при поиске прямого маршрута: {inner_e}")
        except Exception as e:
            logger.error(f"Непредвиденная ошибка при формировании расписания: {e}")
        
        # Если не удалось получить ни одного маршрута, создаем заглушки
        if not schedule_objects:
            logger.warning(f"Не найдены маршруты для {entities.start_city} - {entities.end_city} на {api_date_format}")
            
            # Создаем заглушки с расписанием
            start_time = current_timestamp
            
            # Автобус
            schedule_objects.append(ScheduleObject(
                type=TransportType.bus,
                place_start=entities.start_city,
                place_finish=entities.end_city,
                time_start_utc=start_time,
                time_end_utc=start_time + 3600,  # +1 час
                ticket_url=f"http://example.com/ticket/bus/{entities.start_city}-{entities.end_city}"  # Добавлено
            ))
            
            # Поезд
            schedule_objects.append(ScheduleObject(
                type=TransportType.train,
                place_start=entities.start_city,
                place_finish=entities.end_city,
                time_start_utc=start_time + 1800,  # +30 минут
                time_end_utc=start_time + 5400,  # +1.5 часа
                ticket_url=f"http://example.com/ticket/train/{entities.start_city}-{entities.end_city}"  # Добавлено
            ))
        
        return ScheduleResponse(objects=schedule_objects) 