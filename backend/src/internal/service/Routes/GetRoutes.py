import os
import json
import logging
from typing import Optional, Dict, Any, List

import requests
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class GetRoutes:
    def __init__(self) -> None:
        self.api_key: str = os.getenv("YANDEX_API_KEY", "")
        self.base_url: str = "https://api.rasp.yandex.net/v3.0/"
        self.transport_types = {"plane", "train", "bus"}

    def _get_station_code(self, city_name: str, lang: str = "ru_RU") -> Optional[str]:
        """
        Получает код станции по названию города.

        :param city_name: Название города.
        :param lang: Язык ответа (по умолчанию 'ru_RU').
        :return: Код станции или None, если город не найден.
        """
        url = f"{self.base_url}stations_list/"
        params = {"apikey": self.api_key, "format": "json", "lang": lang}

        try:
            response = requests.get(url, params=params, timeout=20)
            response.raise_for_status()

            for country in response.json().get("countries", []):
                for region in country.get("regions", []):
                    for settlement in region.get("settlements", []):
                        if settlement["title"].lower() == city_name.lower():
                            return settlement["codes"]["yandex_code"]
        except requests.exceptions.RequestException as e:
            logging.error(f"Ошибка при запросе к API: {e}")
        return None

    def get_routes(self, from_city: str, to_city: str, date: str, lang: str = "ru_RU", page: int = 1, prefered_transport: Optional[Dict[str, int]] = None) -> Optional[Dict[str, Any]]:
        """
        Получает список маршрутов между городами на указанную дату.

        :param from_city: Название города отправления.
        :param to_city: Название города назначения.
        :param date: Дата в формате 'YYYY-MM-DD'.
        :param lang: Язык ответа (по умолчанию 'ru_RU').
        :param page: Номер страницы результатов (по умолчанию 1).
        :param prefered_transport: Словарь с предпочтениями по транспорту (например, {"train": 1, "plane": 0, "bus": 0}).
        :return: JSON-ответ с маршрутами или None в случае ошибки.
        """
        from_code = self._get_station_code(from_city, lang)
        to_code = self._get_station_code(to_city, lang)
        if not from_code or not to_code:
            logging.error("Не удалось определить код станции для одного из городов")
            return None

        url = f"{self.base_url}search/"
        params = {"apikey": self.api_key, "format": "json", "from": from_code, "to": to_code, "lang": lang, "page": page, "date": date}

        try:
            response = requests.get(url, params=params, timeout=20)
            response.raise_for_status()
            routes_data = response.json()

            # Если все значения в prefered_transport равны 0, не фильтруем маршруты
            if prefered_transport and not all(value == 0 for value in prefered_transport.values()):
                routes_data = self._filter_routes_by_prefered_transport(routes_data, prefered_transport)

            return routes_data
        except requests.exceptions.RequestException as e:
            logging.error(f"Ошибка при запросе к API: {e}")
            return None

    def _filter_routes_by_prefered_transport(self, routes_data: Dict[str, Any], prefered_transport: Dict[str, int]) -> Dict[str, Any]:
        """
        Фильтрует маршруты по предпочтительным видам транспорта.

        :param routes_data: JSON-данные с маршрутами.
        :param prefered_transport: Словарь с предпочтениями по транспорту.
        :return: Отфильтрованные данные маршрутов.
        """
        if not routes_data or "segments" not in routes_data:
            return routes_data

        filtered_segments = []
        for segment in routes_data["segments"]:
            transport_type = segment.get("thread", {}).get("transport_type")
            if transport_type in prefered_transport and prefered_transport[transport_type] == 1:
                filtered_segments.append(segment)

        routes_data["segments"] = filtered_segments
        return routes_data

    def _get_fastest_routes(self, routes_data: Dict[str, Any], num_routes: int = 6) -> List[Dict[str, Any]]:
        """
        Возвращает заданное количество самых быстрых маршрутов, включая хотя бы один из каждого типа транспорта.

        :param routes_data: JSON-данные с маршрутами.
        :param num_routes: Количество маршрутов, которое нужно вернуть (по умолчанию 6).
        :return: Список самых быстрых маршрутов.
        """
        if not routes_data or "segments" not in routes_data:
            logging.error("Некорректные данные маршрутов")
            return []

        segments = sorted(routes_data["segments"], key=lambda x: x.get("duration", float("inf")))
        transport_groups = {transport: [] for transport in self.transport_types}

        for segment in segments:
            transport_type = segment.get("thread", {}).get("transport_type")
            if transport_type in transport_groups:
                transport_groups[transport_type].append(segment)

        fastest_routes = []
        for transport, routes in transport_groups.items():
            if routes:
                fastest_routes.append(routes[0])

        remaining_slots = num_routes - len(fastest_routes)
        additional_routes = [route for route in segments if route not in fastest_routes][:remaining_slots]
        fastest_routes.extend(additional_routes)

        return fastest_routes[:num_routes]

    def get_aggregated_routes(self, from_city: str, to_city: str, date: str, num_routes: int = 4, prefered_transport: Optional[Dict[str, int]] = None) -> List[Dict[str, Any]]:
        """
        Получает и агрегирует маршруты, возвращая заданное количество самых быстрых.

        :param from_city: Название города отправления.
        :param to_city: Название города назначения.
        :param date: Дата в формате 'YYYY-MM-DD'.
        :param num_routes: Количество маршрутов, которое нужно вернуть (по умолчанию 6).
        :param prefered_transport: Словарь с предпочтениями по транспорту.
        :return: Список агрегированных маршрутов.
        """
        routes_data = self.get_routes(from_city, to_city, date, prefered_transport=prefered_transport)
        if routes_data:
            return self._get_fastest_routes(routes_data, num_routes)
        return []


if __name__ == "__main__":
    yandex_schedule = GetRoutes()
    from_city = "Самара"
    to_city = "Москва"
    date = "2025-09-02"

    fastest_routes = yandex_schedule.get_aggregated_routes(from_city, to_city, date, num_routes=4)
    print(json.dumps(fastest_routes, indent=4, ensure_ascii=False))
