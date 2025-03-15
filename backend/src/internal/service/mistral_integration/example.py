"""
Пример использования модуля интеграции с Mistral AI.
"""

import json
import os
from typing import List

from internal.schemas.redis import RedisMessage, Role
from internal.schemas.responces import ResponseType
from internal.service.mistral_integration import MessageHandler


def create_message(role: str, text: str) -> RedisMessage:
    """Создает объект сообщения для тестирования."""
    return RedisMessage(
        role=Role(role),
        state="",
        text=text
    )


def print_response(response):
    """Выводит ответ в читаемом формате."""
    if response.type == ResponseType.message:
        print(f"\nОтвет системы (сообщение):\n{response.text}\n")
    elif response.type == ResponseType.schedule:
        print(f"\nОтвет системы (расписание):")
        print(f"Найдено {len(response.objects)} вариантов маршрута:")
        
        for i, obj in enumerate(response.objects, 1):
            print(f"  {i}. {obj.type} из {obj.place_start} в {obj.place_finish}")
            print(f"     Время: {obj.time_start_utc} - {obj.time_end_utc}")
            print(f"     Билет: {obj.ticket_url}")


def demo_dialog():
    """Демонстрирует работу модуля на примере диалога."""
    # Создаем обработчик сообщений
    handler = MessageHandler()
    
    # Начальное состояние
    context = json.dumps({"date": "", "start_city": "", "end_city": "", "mid_city": []})
    message_history = [create_message("user", context)]
    
    # Сценарий диалога
    dialogue = [
        "Привет! Я хочу отправиться в путешествие",
        "Хочу поехать из Москвы в Санкт-Петербург",
        "Дата поездки 15.06.2023",
        "А можно через Великий Новгород?"
    ]
    
    # Имитация диалога
    for message_text in dialogue:
        print(f"\nПользователь: {message_text}")
        
        # Обрабатываем сообщение
        response = handler.process_message(message_text, message_history)
        
        # Выводим ответ
        print_response(response)
        
        # Добавляем сообщения в историю
        message_history.append(create_message("user", message_text))
        
        if hasattr(response, 'text'):
            message_history.append(create_message("ai", response.text))
        else:
            # Для расписания добавляем специальное сообщение
            message_history.append(create_message("ai", "Вот найденные варианты маршрута"))


if __name__ == "__main__":
    # Проверяем наличие API ключа (для демонстрации)
    api_key = os.getenv("MISTRAL_API_KEY")
    if not api_key:
        print("Внимание: Переменная окружения MISTRAL_API_KEY не установлена.")
        print("Модуль будет работать с использованием резервных алгоритмов.\n")
    
    # Запускаем демонстрацию
    demo_dialog() 