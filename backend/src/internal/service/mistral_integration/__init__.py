"""
Модуль для интеграции с Mistral AI API для извлечения сущностей из диалога.
"""

from .entities import TravelEntities
from .api_client import MistralAIClient
from .message_handler import MessageHandler
from .extractor import EntityExtractor 