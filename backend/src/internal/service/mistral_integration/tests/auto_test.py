"""
Автоматический тест для MessageHandler.
Выполняет предопределенную серию сообщений и показывает результаты.

Этот скрипт позволяет тестировать MessageHandler без ручного ввода,
имитируя последовательные сообщения пользователя в диалоге.

Запускать с указанием PYTHONPATH:
PYTHONPATH=/path/to/project python3 auto_test.py
"""

import json
import sys
import os
from datetime import datetime

# Добавляем путь к корню проекта для импорта модулей
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..')))

from internal.service.mistral_integration.message_handler import MessageHandler
from internal.service.mistral_integration.entities import TravelEntities


class MockRedisMessage:
    """
    Мок-класс для имитации Redis-сообщений.
    Эмулирует структуру сообщения из Redis, содержащего сериализованные данные.
    """
    
    def __init__(self, content: dict):
        """
        Создает мок-сообщение из словаря с данными.
        
        Args:
            content: Словарь с данными, который будет сериализован в JSON
        """
        self.text = json.dumps(content)


def print_colored(text, color='white'):
    """
    Выводит текст в цвете в консоль.
    
    Args:
        text: Текст для вывода
        color: Цвет текста ('red', 'green', 'yellow', 'blue', 'magenta', 'cyan', 'white')
    """
    colors = {
        'red': '\033[91m',
        'green': '\033[92m',
        'yellow': '\033[93m',
        'blue': '\033[94m',
        'magenta': '\033[95m',
        'cyan': '\033[96m',
        'white': '\033[97m',
    }
    end_color = '\033[0m'
    
    print(f"{colors.get(color, colors['white'])}{text}{end_color}")


def run_test_dialog():
    """
    Выполняет автоматический тестовый диалог.
    
    Тест имитирует последовательные сообщения пользователя:
    1. Указание города отправления
    2. Указание города прибытия
    3. Указание даты поездки
    4. Добавление промежуточного города
    
    На каждом шаге проверяется корректность работы MessageHandler:
    - Извлечение сущностей
    - Формирование ответов
    - Накопление контекста
    """
    print_colored("=== Автоматический тест MessageHandler ===", 'cyan')
    print_colored("Симуляция диалога с предопределенными сообщениями пользователя", 'cyan')
    print()
    
    # Тестовые сообщения - последовательность диалога
    test_messages = [
        "Хочу поехать из Москвы",                # Только город отправления
        "в Санкт-Петербург",                     # Добавляем город прибытия
        "1 мая 2025 года",                       # Добавляем дату
        "а можно через Тверь?"                   # Добавляем промежуточный город
    ]
    
    # Инициализируем MessageHandler
    try:
        handler = MessageHandler()
        print_colored("✓ MessageHandler инициализирован успешно", 'green')
    except Exception as e:
        print_colored(f"✗ Ошибка при инициализации MessageHandler: {e}", 'red')
        return
    
    # История сообщений (имитация контекста диалога)
    message_history = []
    
    # Сущности, извлеченные из сообщений
    entities = TravelEntities()
    
    # Выполняем тестовый диалог
    for i, message in enumerate(test_messages):
        print_colored(f"\n--- Шаг {i+1}: Обработка сообщения ---", 'blue')
        print_colored(f"Пользователь > {message}", 'white')
        
        # Обрабатываем сообщение
        try:
            print_colored("Обработка сообщения...", 'blue')
            result = handler.process_message(message, message_history)
            
            # Выводим результат обработки
            if hasattr(result, 'text'):
                # Это MessageResponse (уточняющий вопрос)
                print_colored(f"Система > {result.text}", 'green')
            else:
                # Это ScheduleResponse (расписание маршрутов)
                print_colored("Система > Получено расписание:", 'green')
                for j, obj in enumerate(result.objects):
                    print_colored(f"  {j+1}. {obj.type.name} из {obj.place_start} в {obj.place_finish}", 'green')
                    start_time = datetime.fromtimestamp(obj.time_start_utc).strftime('%H:%M:%S %d.%m.%Y')
                    end_time = datetime.fromtimestamp(obj.time_end_utc).strftime('%H:%M:%S %d.%m.%Y')
                    print_colored(f"     Отправление: {start_time}", 'green')
                    print_colored(f"     Прибытие: {end_time}", 'green')
            
            # Извлекаем сущности из последнего ответа и обновляем накопленные данные
            extractor = handler.entity_extractor
            entities = extractor.extract_entities(message, entities)
            
            # Обновляем историю сообщений
            message_history = [MockRedisMessage(entities.to_dict())]
            
            # Выводим текущее состояние сущностей
            print()
            print_colored("Текущие сущности:", 'magenta')
            for key, value in entities.to_dict().items():
                print_colored(f"  {key}: {value}", 'magenta')
            
        except Exception as e:
            # Обработка ошибок
            print_colored(f"✗ Ошибка при обработке сообщения: {e}", 'red')
            import traceback
            print_colored(traceback.format_exc(), 'red')
    
    print()
    print_colored("=== Тест завершен ===", 'cyan')


if __name__ == "__main__":
    run_test_dialog() 