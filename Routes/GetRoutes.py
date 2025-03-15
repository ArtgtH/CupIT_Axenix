import requests
import json
import os

from dotenv import load_dotenv

load_dotenv()

# os.getenv('YANDEX_API_KEY')
class GetRoutes:
    def __init__(self):
        self.api_key = os.getenv('YANDEX_API_KEY')
        self.base_url = "https://api.rasp.yandex.net/v3.0/"
    
    def get_station_code(self, city_name, lang="ru_RU"):
        """
        Получает код станции по названию города.
        
        :param city_name: Название города (например, 'Москва').
        :param lang: Язык ответа (по умолчанию 'ru_RU').
        :return: Код станции или None, если город не найден.
        """
        url = f"{self.base_url}stations_list/"
        params = {
            "apikey": self.api_key,
            "format": "json",
            "lang": lang
        }
        
        try:
            response = requests.get(url, params=params, timeout=20)
            response.raise_for_status()
            data = response.json()
            for country in data.get("countries", []):
                for region in country.get("regions", []):
                    for settlement in region.get("settlements", []):
                        if settlement["title"].lower() == city_name.lower():
                            return settlement["codes"]["yandex_code"]
            return None
        except requests.exceptions.RequestException as e:
            raise Exception(f"Ошибка при запросе к API: {e}")
    
    def get_routes(self, from_city, to_city, date, lang="ru_RU", page=1, save_to_file=False):
        """
        Получает список маршрутов между пунктами отправления и назначения на указанную дату.
        
        :param from_city: Название города отправления.
        :param to_city: Название города назначения.
        :param date: Дата в формате 'YYYY-MM-DD'.
        :param lang: Язык ответа (по умолчанию 'ru_RU').
        :param page: Номер страницы (по умолчанию 1).
        :param save_to_file: Флаг для сохранения результата в файл JSON.
        :return: JSON с результатами маршрутов.
        """
        from_code = self.get_station_code(from_city, lang)
        to_code = self.get_station_code(to_city, lang)
        
        if not from_code or not to_code:
            raise Exception("Не удалось определить код станции для одного из городов")
        
        url = f"{self.base_url}search/"
        params = {
            "apikey": self.api_key,
            "format": "json",
            "from": from_code,
            "to": to_code,
            "lang": lang,
            "page": page,
            "date": date
        }
        
        try:
            response = requests.get(url, params=params, timeout=20)
            response.raise_for_status()
            result = response.json()
            
            if save_to_file:
                with open("routes.json", "w", encoding="utf-8") as file:
                    json.dump(result, file, indent=4, ensure_ascii=False)
            
            return result
        except requests.exceptions.RequestException as e:
            raise Exception(f"Ошибка при запросе к API: {e}")

# Пример использования
if __name__ == "__main__":
    yandex_schedule = GetRoutes()
    from_city = "Самара"  # Город отправления
    to_city = "Москва"  # Город назначения
    date = "2025-09-02" # Дата
    lang = "ru_RU"      # Язык ответа
    page = 1            # Номер страницы
    save_to_file = True  # Флаг для сохранения в файл
    
    try:
        routes = yandex_schedule.get_routes(from_city, to_city, date, lang, page, save_to_file)
        print(json.dumps(routes, indent=4, ensure_ascii=False))
    except Exception as e:
        print(e)
