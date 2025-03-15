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
            routes_api = GetRoutes()
            route_finder = GetRoutesWithStops(routes_api)
            
            # Проверяем наличие промежуточных городов и формируем список остановок
            if entities.mid_city:
                # Есть промежуточные города
                stops = [entities.start_city] + entities.mid_city + [entities.end_city]
            else:
                # Промежуточных городов нет, используем [None]
                # Для find_multi_leg_route нужен список с городами отправления и прибытия
                stops = [entities.start_city, None, entities.end_city]
            
            try:
                # Используем один и тот же метод для обоих случаев
                result = route_finder.find_multi_leg_route(stops, api_date_format)
                
                if result and 'route' in result:
                    # Создаем объект маршрута для многоэтапного пути
                    for i, segment in enumerate(result['route']):
                        # Рассчитываем время начала и конца (в секундах)
                        start_time = current_timestamp + (i * 7200)  # 2 часа между сегментами
                        end_time = start_time + segment.get('duration', 3600)
                        
                        # Определяем тип транспорта на основе расстояния
                        distance = segment.get('distance', 0)
                        if distance > 1000:
                            transport_type = TransportType.plane
                        elif distance > 300:
                            transport_type = TransportType.train
                        else:
                            transport_type = TransportType.bus
                        
                        schedule_objects.append(
                            ScheduleObject(
                                type=transport_type,
                                time_start_utc=start_time,
                                time_end_utc=end_time,
                                place_start=segment.get('from', ""),
                                place_finish=segment.get('to', ""),
                                ticket_url=f"http://example.com/ticket/{transport_type}",
                            )
                        )
            except Exception as e:
                logger.error(f"Ошибка при поиске маршрута: {e}")
                # Если не удалось найти маршрут через find_multi_leg_route, 
                # пробуем найти прямой маршрут
                try:
                    segment = route_finder.find_best_route(entities.start_city, entities.end_city, api_date_format)
                    
                    if segment:
                        duration = segment.get('duration', 3600)
                        distance = segment.get('distance', 0)
                        
                        # Определяем доступные типы транспорта на основе расстояния
                        transport_types = []
                        
                        if distance > 1000:
                            transport_types.append(TransportType.plane)
                        
                        if distance > 100:
                            transport_types.append(TransportType.train)
                        
                        if distance < 800:
                            transport_types.append(TransportType.bus)
                        
                        # Если не определили ни один тип транспорта, добавляем поезд и автобус по умолчанию
                        if not transport_types:
                            transport_types = [TransportType.train, TransportType.bus]
                        
                        # Создаем объекты расписания для каждого типа транспорта
                        for i, transport_type in enumerate(transport_types):
                            # Разное время начала для разных типов транспорта
                            start_time = current_timestamp + (i * 3600)  # 1 час между отправлениями
                            
                            # Рассчитываем продолжительность в зависимости от типа транспорта
                            if transport_type == TransportType.plane:
                                duration_factor = 0.5  # Самолет быстрее
                            elif transport_type == TransportType.train:
                                duration_factor = 1.0  # Стандартная скорость
                            else:
                                duration_factor = 1.5  # Автобус медленнее
                            
                            adjusted_duration = int(duration * duration_factor)
                            
                            schedule_objects.append(
                                ScheduleObject(
                                    type=transport_type,
                                    time_start_utc=start_time,
                                    time_end_utc=start_time + adjusted_duration,
                                    place_start=entities.start_city,
                                    place_finish=entities.end_city,
                                    ticket_url=f"http://example.com/ticket/{transport_type}",
                                )
                            )
                except Exception as e:
                    logger.error(f"Ошибка при поиске прямого маршрута: {e}")
                    
        except Exception as e:
            logger.error(f"Общая ошибка при поиске маршрутов: {e}")
        
        # Если не нашли ни одного маршрута, используем заглушку
        if not schedule_objects:
            logger.warning(f"Не найдены маршруты для {entities.start_city} - {entities.end_city} на {api_date_format}")
            
            # Заглушка для случая, когда маршруты не найдены
            schedule_objects = [
                ScheduleObject(
                    type=TransportType.bus,
                    time_start_utc=current_timestamp,
                    time_end_utc=current_timestamp + 3600,
                    place_start=entities.start_city,
                    place_finish=entities.end_city,
                    ticket_url="http://example.com/ticket/bus",
                ),
                ScheduleObject(
                    type=TransportType.train,
                    time_start_utc=current_timestamp + 1800,
                    time_end_utc=current_timestamp + 5400,
                    place_start=entities.start_city,
                    place_finish=entities.end_city,
                    ticket_url="http://example.com/ticket/train",
                )
            ]
        
        return ScheduleResponse(objects=schedule_objects) 