# Модуль интеграции с Mistral AI

Этот модуль обеспечивает интеграцию с Mistral AI API для извлечения сущностей из диалога с пользователем.

## Структура модуля

- `__init__.py` - файл инициализации пакета
- `config.py` - настройки для Mistral AI API
- `entities.py` - класс для управления сущностями путешествия
- `api_client.py` - клиент для работы с Mistral AI API
- `extractor.py` - класс для извлечения сущностей с резервными алгоритмами
- `message_handler.py` - обработчик сообщений и формирование ответов

## Настройка

Для работы модуля необходимо указать API-ключ Mistral AI в переменных окружения:

```bash
export MISTRAL_API_KEY=your_api_key_here
```

Дополнительные параметры (опционально):
```bash
export MISTRAL_API_URL=https://api.mistral.ai/v1/chat/completions
export MISTRAL_MODEL_NAME=mistral-large-latest
export MISTRAL_TEMPERATURE=0.1
export MISTRAL_MAX_TOKENS=500
```

## Использование

### Основной интерфейс

```python
from internal.service.mistral_integration import MessageHandler

# Создание обработчика сообщений
handler = MessageHandler()

# Обработка входящего сообщения
response = handler.process_message(input_text, message_history)

# Ответ будет либо ScheduleResponse, либо MessageResponse
if response.type == "schedule":
    # Показываем расписание
    print(f"Найдено {len(response.objects)} вариантов маршрута")
else:
    # Показываем сообщение с уточнением
    print(response.text)
```

### Прямое использование экстрактора сущностей

```python
from internal.service.mistral_integration import EntityExtractor, TravelEntities

# Создание экстрактора сущностей
extractor = EntityExtractor()

# Текущие сущности (можно создать пустой объект)
current_entities = TravelEntities()

# Извлечение сущностей из сообщения
updated_entities = extractor.extract_entities("Хочу поехать из Москвы в Санкт-Петербург 15.06.2023", current_entities)

# Проверка полноты данных
if updated_entities.is_complete():
    print("Все необходимые данные получены")
else:
    print(f"Отсутствуют данные: {updated_entities.get_missing_entities()}")
```

## Отказоустойчивость

Модуль обеспечивает отказоустойчивость в случае недоступности Mistral AI API:

1. Сначала пытается использовать API для точного извлечения сущностей
2. В случае ошибки использует встроенные алгоритмы на базе регулярных выражений
3. Логирует все ошибки и процесс извлечения сущностей

## Расширение функциональности

Для добавления новых сущностей для извлечения:

1. Обновите класс `TravelEntities` в файле `entities.py`
2. Добавьте новые шаблоны в методы `_extract_*` класса `EntityExtractor`
3. Обновите промпт в методе `_build_extraction_prompt` класса `MistralAIClient` 