from .GetRoutes import GetRoutes

class GetRoutesWithStops:
    def __init__(self, routes_api: GetRoutes):
        self.routes_api = routes_api

    def find_best_route(self, start: str, end: str, date: str):
        """
        Находит лучший маршрут между двумя городами на указанную дату.
        
        :param start: Город отправления.
        :param end: Город назначения.
        :param date: Дата в формате 'YYYY-MM-DD'.
        :return: Лучший маршрут (с минимальной продолжительностью) или None, если маршруты не найдены.
        """
        routes_data = self.routes_api.get_routes(start, end, date)
        
        # Проверяем, есть ли данные о маршрутах
        if not routes_data or "segments" not in routes_data:
            return None
        
        # Извлекаем сегменты маршрутов
        segments = routes_data["segments"]
        
        # Если сегментов нет, возвращаем None
        if not segments:
            return None
        
        # Выбираем маршрут с минимальной продолжительностью
        best_segment = min(segments, key=lambda s: s.get("duration", float('inf')))
        return best_segment

    def find_multi_leg_route(self, stops: list, date: str):
        """
        Находит маршрут с несколькими остановками.
        
        :param stops: Список городов (например, ["Москва", "Тверь", "Санкт-Петербург"]).
        :param date: Дата в формате 'YYYY-MM-DD'.
        :return: Словарь с полным маршрутом, общей продолжительностью и расстоянием.
        """
        full_route = []
        total_duration = 0
        total_distance = 0
        
        for i in range(len(stops) - 1):
            segment = self.find_best_route(stops[i], stops[i + 1], date)
            if not segment:
                return None  # Если одного из сегментов нет, возвращаем None
            
            full_route.append({
                'from': stops[i],
                'to': stops[i + 1],
                'duration': segment.get("duration", 0),
                'distance': segment.get("distance", 0)
            })
            total_duration += segment.get("duration", 0)
            total_distance += segment.get("distance", 0)
        
        return {
            'route': full_route,
            'total_duration': total_duration,
            'total_distance': total_distance
        }

# Пример использования
if __name__ == "__main__":
    routes_api = GetRoutes()
    route_finder = GetRoutesWithStops(routes_api)
    
    stops = ["Москва", "Тверь", "Санкт-Петербург"]
    date = "2025-03-15"
    result = route_finder.find_multi_leg_route(stops, date)
    print(result)