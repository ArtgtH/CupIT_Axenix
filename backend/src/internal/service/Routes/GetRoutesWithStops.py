import logging
from typing import Optional, List, Dict, Any

from .GetRoutes import GetRoutes

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class GetRoutesWithStops:
    """
    Класс для поиска оптимальных маршрутов между городами,
    включая поддержку многоэтапных маршрутов.
    """
    def __init__(self) -> None:
        self.routes_api = GetRoutes()

    def _find_best_routes(
        self, start: str, end: str, date: str, top_n: int = 3
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Находит несколько лучших маршрутов между двумя городами на указанную дату.

        :param start: Город отправления.
        :param end: Город назначения.
        :param date: Дата в формате 'YYYY-MM-DD'.
        :param top_n: Количество лучших маршрутов для возврата (по умолчанию 3).
        :return: Список топ-N маршрутов с наименьшей продолжительностью или None.
        """
        logging.info(f"Поиск маршрутов: {start} -> {end} на {date}")
        routes_data = self.routes_api.get_routes(start, end, date)

        if not routes_data or "segments" not in routes_data:
            logging.warning(f"Маршруты не найдены: {start} -> {end} на {date}")
            return None

        segments = routes_data["segments"]

        if not segments:
            logging.warning(f"Сегменты отсутствуют: {start} -> {end} на {date}")
            return None

        best_routes = sorted(segments, key=lambda s: s.get("duration", float("inf")))[:top_n]
        logging.info(f"Найдено {len(best_routes)} лучших маршрутов")
        return best_routes

    def find_multi_leg_route(self, stops: List[str], date: str) -> Optional[Dict[str, Any]]:
        """
        Находит маршрут с несколькими остановками.

        :param stops: Список городов (например, ["Москва", "Тверь", "Санкт-Петербург"]).
        :param date: Дата в формате 'YYYY-MM-DD'.
        :return: Словарь с полным маршрутом, общей продолжительностью и расстоянием или None.
        """
        logging.info(f"Поиск маршрута с остановками: {stops} на {date}")
        full_route = []
        total_duration = 0
        total_distance = 0

        for i in range(len(stops) - 1):
            best_routes = self._find_best_routes(stops[i], stops[i + 1], date)
            if not best_routes:
                logging.error(f"Не удалось найти маршрут между {stops[i]} и {stops[i + 1]} на {date}")
                return None

            full_route.append({
                "from": stops[i],
                "to": stops[i + 1],
                "routes": best_routes  # Сохраняем полную информацию о маршрутах
            })
            total_duration += best_routes[0].get("duration", 0)
            total_distance += best_routes[0].get("distance", 0)

        logging.info(f"Маршрут успешно найден: {full_route}")
        return {
            "route": full_route,
            "total_duration": total_duration,
            "total_distance": total_distance,
        }


if __name__ == "__main__":
    route_finder = GetRoutesWithStops()

    stops_list = ["Москва", "Тверь", "Санкт-Петербург"]
    travel_date = "2025-03-15"
    result = route_finder.find_multi_leg_route(stops_list, travel_date)
