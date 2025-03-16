from typing import List, Dict, Any, Optional
import json
import re
import requests
from datetime import datetime
import os

from internal.schemas.redis import RedisMessage
from internal.schemas.responces import (
    ScheduleResponse,
    ScheduleObject,
    TransportType,
    MessageResponse,
)

from internal.service.mistral_integration.message_handler import MessageHandler

def talk_with_god(
    input_text: str, thread: List[RedisMessage]
) -> ScheduleResponse | MessageResponse:
    """
    Функция для общения с пользователем и извлечения сущностей о маршруте.
    Использует MessageHandler для обработки истории сообщений.
    
    Args:
        input_text: Текст запроса пользователя
        thread: История сообщений
        
    Returns:
        ScheduleResponse, если все сущности извлечены
        MessageResponse, если требуется уточнение
    """
    # Создаем обработчик сообщений или получаем существующий экземпляр
    handler = MessageHandler.get_instance()
    
    # Добавляем текущий запрос пользователя к истории сообщений
    current_message = RedisMessage(text=input_text)
    full_thread = thread + [current_message]
    
    # Обрабатываем историю сообщений и получаем ответ
    return handler.process_message(full_thread)
