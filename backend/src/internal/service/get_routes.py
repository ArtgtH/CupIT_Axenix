import logging
from datetime import datetime
from typing import List, Optional, Dict

from internal.schemas.responces import ScheduleResponse, ScheduleObject, TransportType


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_routes(points: List[str], date: str, prefered_transport: Optional[Dict[str, int]] = None) -> Optional[ScheduleResponse]:
    """
    Получает маршруты между точками и возвращает их в формате ScheduleResponse.

    :param points: Список городов (точек) для построения маршрута.
    :param date: Дата в формате 'YYYY-MM-DD'.
    :param prefered_transport: Словарь с предпочтениями по транспорту (например, {"train": 1, "plane": 0, "bus": 0}).
    :return: Объект ScheduleResponse с маршрутами или None в случае ошибки.
    """
    if len(points) < 2:
        logger.error("Необходимо как минимум две точки для построения маршрута")
        raise ValueError("Необходимо как минимум две точки для построения маршрута")

    try:
        if len(points) == 2:
            # Используем GetRoutes для двух точек
            logger.info(f"Поиск маршрута между {points[0]} и {points[1]} на {date}")
            routes_api = GetRoutes()

            # Если все предпочтения равны 0, не передаем prefered_transport
            if prefered_transport and all(value == 0 for value in prefered_transport.values()):
                prefered_transport = None

            routes_data = routes_api.get_aggregated_routes(points[0], points[1], date, prefered_transport=prefered_transport)

            if not routes_data:
                logger.error("Не удалось получить данные маршрутов")
                return None

            schedule_objects = []
            for route in routes_data:
                if "thread" not in route:
                    logger.error("Некорректная структура данных маршрута")
                    continue

                transport_type = TransportType[route["thread"]["transport_type"]]
                schedule_object = ScheduleObject(
                    type=transport_type,
                    time_start_utc=int(datetime.fromisoformat(route["departure"]).timestamp()),
                    time_end_utc=int(datetime.fromisoformat(route["arrival"]).timestamp()),
                    place_start=route["from"]["title"],
                    place_finish=route["to"]["title"],
                    ticket_url="",  # Пропускаем ticket_url, если tickets_info отсутствует
                )
                schedule_objects.append(schedule_object)

        else:
            # Используем GetRoutesWithStops для более чем двух точек
            logger.info(f"Поиск многоэтапного маршрута через точки: {points} на {date}")
            routes_api = GetRoutesWithStops()

            # Если все предпочтения равны 0, не передаем prefered_transport
            if prefered_transport and all(value == 0 for value in prefered_transport.values()):
                prefered_transport = None

            multi_leg_route = routes_api.find_multi_leg_route(points, date, prefered_transport=prefered_transport)

            if not multi_leg_route:
                logger.error("Не удалось получить данные многоэтапного маршрута")
                return None

            schedule_objects = []
            for leg in multi_leg_route["route"]:
                for route in leg["routes"]:
                    if "thread" not in route:
                        logger.error("Некорректная структура данных маршрута")
                        continue

                    transport_type = TransportType[route["thread"]["transport_type"]]
                    schedule_object = ScheduleObject(
                        type=transport_type,
                        time_start_utc=int(datetime.fromisoformat(route["departure"]).timestamp()),
                        time_end_utc=int(datetime.fromisoformat(route["arrival"]).timestamp()),
                        place_start=route["from"]["title"],
                        place_finish=route["to"]["title"],
                        ticket_url="",  # Пропускаем ticket_url, если tickets_info отсутствует
                    )
                    schedule_objects.append(schedule_object)

        return ScheduleResponse(type="schedule", objects=schedule_objects)

    except Exception as e:
        logger.error(f"Ошибка при получении маршрутов: {e}")
        return None
