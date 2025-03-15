"""
Клиент для работы с Mistral AI API.
"""

import json
import logging
from typing import Dict, Any, List, Optional

import requests
from requests.exceptions import RequestException

from .config import settings


logger = logging.getLogger(__name__)


class APIError(Exception):
    """Ошибка при взаимодействии с Mistral AI API."""
    pass


class MistralAIClient:
    """
    Клиент для работы с Mistral AI API.
    Обеспечивает взаимодействие с API для извлечения сущностей из текста.
    """
    
    def __init__(self, api_key: Optional[str] = None, api_url: Optional[str] = None, 
                 model_name: Optional[str] = None):
        """
        Инициализирует клиент для работы с Mistral AI API.
        
        Args:
            api_key: API ключ для Mistral AI (если не указан, берется из настроек)
            api_url: URL API Mistral AI (если не указан, берется из настроек)
            model_name: Название модели Mistral AI (если не указано, берется из настроек)
        """
        self.api_key = api_key or settings.API_KEY
        self.api_url = api_url or settings.API_URL
        self.model_name = model_name or settings.MODEL_NAME
        
        if not self.api_key:
            logger.warning("Mistral AI API ключ не предоставлен. API вызовы не будут выполняться.")
    
    def extract_entities(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Извлекает сущности из сообщения пользователя с помощью Mistral AI.
        
        Args:
            message: Текст сообщения пользователя
            context: Контекст, содержащий текущие значения сущностей
            
        Returns:
            Словарь с извлеченными сущностями
            
        Raises:
            APIError: если произошла ошибка при обращении к API
        """
        if not self.api_key:
            logger.error("Невозможно выполнить запрос: API ключ не предоставлен")
            raise APIError("API ключ Mistral AI не настроен")
        
        # Формируем промпт для модели
        prompt = self._build_extraction_prompt(message, context)
        
        try:
            response = requests.post(
                self.api_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model_name,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": settings.TEMPERATURE,
                    "max_tokens": settings.MAX_TOKENS
                },
                timeout=15  # Таймаут 15 секунд
            )
            
            response.raise_for_status()
            result = response.json()
            
            # Извлекаем ответ модели
            content = result["choices"][0]["message"]["content"]
            logger.debug(f"Mistral AI ответ: {content}")
            
            # Парсим JSON ответ
            try:
                extracted_data = json.loads(content)
                return extracted_data
            except json.JSONDecodeError as e:
                logger.error(f"Ошибка парсинга JSON из ответа Mistral AI: {e}. Ответ: {content}")
                raise APIError(f"Ошибка парсинга ответа Mistral AI: {e}")
            
        except RequestException as e:
            logger.error(f"Ошибка запроса к Mistral AI API: {e}")
            raise APIError(f"Ошибка соединения с Mistral AI: {e}")
        except KeyError as e:
            logger.error(f"Некорректный формат ответа от Mistral AI API: {e}")
            raise APIError(f"Некорректный формат ответа от Mistral AI: {e}")
        except Exception as e:
            logger.error(f"Неожиданная ошибка при обращении к Mistral AI API: {e}")
            raise APIError(f"Непредвиденная ошибка при работе с Mistral AI: {e}")
    
    def _build_extraction_prompt(self, message: str, context: Dict[str, Any]) -> str:
        """
        Формирует промпт для извлечения сущностей.
        
        Args:
            message: Текст сообщения пользователя
            context: Текущие извлеченные сущности
            
        Returns:
            Текст промпта для модели
        """
        return f"""
        # Задача
        Ты - система извлечения информации из сообщений пользователя. Твоя задача - извлечь следующие сущности из текста пользователя:
        
        - date: Дата в формате dd.mm.yyyy
        - start_city: Город отправления на русском языке
        - end_city: Город прибытия на русском языке
        - mid_city: Список промежуточных городов на русском языке (может быть пустым)
        
        # Текущие данные
        Текущие извлеченные сущности:
        {json.dumps(context, ensure_ascii=False, indent=2)}
        
        # Сообщение пользователя
        {message}
        
        # Инструкции
        1. Проанализируй текст и выдели упомянутые сущности
        2. Возьми из текста только четко указанные данные
        3. Если сущность уже есть в текущих данных и не упоминается в новом сообщении, сохрани существующее значение
        4. Верни ТОЛЬКО JSON-объект без пояснений. Формат:
        {{
          "date": "дд.мм.гггг",
          "start_city": "город отправления",
          "end_city": "город прибытия",
          "mid_city": ["промежуточный город 1", "промежуточный город 2"]
        }}
        
        Если сущность не найдена и нет в текущих данных, оставь пустую строку или пустой массив для mid_city.
        """ 