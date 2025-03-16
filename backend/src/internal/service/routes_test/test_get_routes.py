import unittest
from datetime import datetime
from typing import List

from internal.schemas.responces import ScheduleResponse, ScheduleObject, TransportType
from internal.service.routes.GetRoutes import GetRoutes
from internal.service.routes.GetRoutesWithStops import GetRoutesWithStops
from internal.service.get_routes import get_routes


class TestGetScheduleResponse(unittest.TestCase):
    def setUp(self):
        """Настройка тестового окружения."""
        self.points_2 = ["Москва", "Санкт-Петербург"]
        self.points_3 = ["Москва", "Тверь", "Санкт-Петербург"]
        self.points_4 = ["Москва", "Тверь", "Великий Новгород", "Санкт-Петербург"]
        self.points_5 = ["Москва", "Тверь", "Великий Новгород", "Псков", "Санкт-Петербург"]
        self.date = "2025-03-20"

    def test_two_points(self):
        """Тест для двух точек."""
        response = get_routes(self.points_2, self.date)
        self.assertIsInstance(response, ScheduleResponse)
        self.assertEqual(response.type, "schedule")
        self.assertGreater(len(response.objects), 0)

    def test_three_points(self):
        """Тест для трех точек."""
        response = get_routes(self.points_3, self.date)
        self.assertIsInstance(response, ScheduleResponse)
        self.assertEqual(response.type, "schedule")
        self.assertGreater(len(response.objects), 0)

    def test_four_points(self):
        """Тест для четырех точек."""
        response = get_routes(self.points_4, self.date)
        self.assertIsInstance(response, ScheduleResponse)
        self.assertEqual(response.type, "schedule")
        self.assertGreater(len(response.objects), 0)

    def test_five_points(self):
        """Тест для пяти точек."""
        response = get_routes(self.points_5, self.date)
        self.assertIsInstance(response, ScheduleResponse)
        self.assertEqual(response.type, "schedule")
        self.assertGreater(len(response.objects), 0)

    def test_invalid_points(self):
        """Тест для невалидного количества точек (меньше 2)."""
        with self.assertRaises(ValueError):
            get_routes(["Москва"], self.date)

    def test_invalid_date(self):
        """Тест для невалидной даты."""
        with self.assertRaises(Exception):  # Ожидаем ошибку, если дата некорректна
            get_routes(self.points_2, "некорректная дата")


if __name__ == "__main__":
    unittest.main()
