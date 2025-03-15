"""
Модуль для работы с сущностями путешествия.
"""

from typing import Dict, Any, Optional, List


class TravelEntities:
    """
    Класс для хранения и управления извлеченными сущностями путешествия.
    Содержит информацию о дате, городах отправления, назначения и промежуточных пунктах.
    """
    
    def __init__(self, data: Optional[Dict[str, Any]] = None):
        """
        Инициализирует объект сущностей путешествия.
        
        Args:
            data: Словарь с исходными данными сущностей
        """
        self.date: str = data.get("date", "") if data else ""
        self.start_city: str = data.get("start_city", "") if data else ""
        self.end_city: str = data.get("end_city", "") if data else ""
        self.mid_city: List[str] = data.get("mid_city", []) if data else []
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Преобразует объект в словарь.
        
        Returns:
            Словарь с сущностями
        """
        return {
            "date": self.date,
            "start_city": self.start_city,
            "end_city": self.end_city,
            "mid_city": self.mid_city
        }
    
    def is_complete(self) -> bool:
        """
        Проверяет, все ли необходимые сущности извлечены.
        
        Returns:
            True, если все обязательные сущности заполнены
        """
        return bool(self.date and self.start_city and self.end_city)
    
    def get_missing_entities(self) -> List[str]:
        """
        Возвращает список отсутствующих сущностей.
        
        Returns:
            Список названий отсутствующих сущностей
        """
        missing = []
        if not self.date:
            missing.append("date")
        if not self.start_city:
            missing.append("start_city")
        if not self.end_city:
            missing.append("end_city")
        return missing
    
    def update(self, new_entities: Dict[str, Any]) -> None:
        """
        Обновляет сущности новыми значениями, если они не пустые.
        
        Args:
            new_entities: Словарь с новыми значениями сущностей
        """
        if new_entities.get("date"):
            self.date = new_entities["date"]
            
        if new_entities.get("start_city"):
            self.start_city = new_entities["start_city"]
            
        if new_entities.get("end_city"):
            self.end_city = new_entities["end_city"]
            
        if new_entities.get("mid_city"):
            # Объединяем списки промежуточных городов, удаляя дубликаты
            mid_cities = set(self.mid_city)
            for city in new_entities["mid_city"]:
                mid_cities.add(city)
            self.mid_city = list(mid_cities)
    
    def get_route_description(self) -> str:
        """
        Формирует текстовое описание маршрута.
        
        Returns:
            Строка с описанием маршрута
        """
        cities = [self.start_city]
        if self.mid_city:
            cities.extend(self.mid_city)
        cities.append(self.end_city)
        
        return " → ".join(cities) 