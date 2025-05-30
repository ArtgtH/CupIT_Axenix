"""
Клиент для работы с Mistral AI API.
"""

import json
import logging
import time
from typing import Dict, Any, Optional
from datetime import datetime
from threading import Lock

import requests
from requests.exceptions import RequestException

from mistralai import Mistral
from .config import settings


logger = logging.getLogger(__name__)


class APIError(Exception):
    """Ошибка при взаимодействии с Mistral AI API."""
    pass


class RateLimiter:
    """
    Класс для ограничения количества запросов в секунду (RPS).
    Реализует алгоритм токенного ведра для контроля частоты запросов.
    """
    
    def __init__(self, max_rps: float = 1.0):
        """
        Инициализирует ограничитель запросов.
        
        Args:
            max_rps: Максимальное количество запросов в секунду
        """
        self.max_rps = max_rps
        self.tokens = max_rps  # Начальное количество токенов равно максимуму
        self.last_check = time.time()
        self.lock = Lock()  # Для потокобезопасности
    
    def acquire(self) -> float:
        """
        Запрашивает разрешение на выполнение запроса.
        Блокирует вызывающий поток, если запросы идут слишком часто.
        
        Returns:
            Время ожидания в секундах
        """
        with self.lock:
            current_time = time.time()
            time_passed = current_time - self.last_check
            self.last_check = current_time
            
            # Пополняем токены с учетом прошедшего времени
            self.tokens = min(self.max_rps, self.tokens + time_passed * self.max_rps)
            
            if self.tokens < 1.0:
                # Не хватает токенов - нужно подождать
                wait_time = (1.0 - self.tokens) / self.max_rps
                time.sleep(wait_time)
                self.tokens = 0.0
                return wait_time
            else:
                # Токенов достаточно - можно выполнить запрос
                self.tokens -= 1.0
                return 0.0


class MistralAIClient:
    """
    Клиент для работы с Mistral AI API.
    Обеспечивает взаимодействие с API для извлечения сущностей из текста.
    """
    # Единственный экземпляр ограничителя запросов для всех клиентов
    _rate_limiter = None
    _rate_limiter_lock = Lock()
    
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
        
        # Инициализируем ограничитель запросов, если еще не создан
        with self._rate_limiter_lock:
            if MistralAIClient._rate_limiter is None:
                MistralAIClient._rate_limiter = RateLimiter(settings.MAX_RPS)
                logger.info(f"Инициализирован ограничитель запросов с лимитом {settings.MAX_RPS} RPS")
        
        if not self.api_key:
            logger.warning("Mistral AI API ключ не предоставлен. API вызовы не будут выполняться.")
        
        # Создаем клиент SDK если доступен
        self.client = None
        if self.api_key:
            try:
                self.client = Mistral(api_key=self.api_key)
                logger.info(f"Клиент Mistral SDK успешно инициализирован с моделью: {self.model_name}")
            except Exception as e:
                logger.error(f"Ошибка инициализации клиента Mistral SDK: {e}")
                self.client = None
    
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
        
        # Ограничиваем частоту запросов
        wait_time = self._rate_limiter.acquire()
        if wait_time > 0:
            logger.debug(f"Запрос к Mistral AI отложен на {wait_time:.2f} сек из-за ограничения RPS")
        
        # Основная логика: сначала пробуем SDK, затем REST API как резервный вариант
        try:
            # Пробуем использовать SDK если доступен
            if self.client:
                try:
                    response = self.client.chat.complete(
                        model=self.model_name,
                        messages=[{"role": "user", "content": prompt}],
                        temperature=settings.TEMPERATURE,
                        max_tokens=settings.MAX_TOKENS,
                        response_format={"type": "json_object"}
                    )
                    
                    content = response.choices[0].message.content
                    logger.debug(f"Mistral AI ответ (SDK): {content}")
                    
                    extracted_data = json.loads(content)
                    return extracted_data
                except Exception as e:
                    if "429" in str(e):
                        # Обработка превышения лимита запросов
                        retry_after = settings.THROTTLE_TIME
                        logger.warning(f"Превышен лимит запросов к Mistral AI. Повтор через {retry_after} сек.")
                        time.sleep(retry_after)
                        
                        # Повторная попытка после ожидания
                        response = self.client.chat.complete(
                            model=self.model_name,
                            messages=[{"role": "user", "content": prompt}],
                            temperature=settings.TEMPERATURE,
                            max_tokens=settings.MAX_TOKENS,
                            response_format={"type": "json_object"}
                        )
                        
                        content = response.choices[0].message.content
                        extracted_data = json.loads(content)
                        return extracted_data
                    else:
                        logger.error(f"Ошибка SDK Mistral: {e}")
                        raise APIError(f"Ошибка при работе с API Mistral: {e}")
            
            # Резервный вариант: REST API если SDK не доступен
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
                    "max_tokens": settings.MAX_TOKENS,
                    "response_format": {"type": "json_object"}
                },
                timeout=15
            )
            
            # Обработка HTTP 429 (слишком много запросов)
            if response.status_code == 429:
                retry_after = int(response.headers.get('Retry-After', settings.THROTTLE_TIME))
                logger.warning(f"Превышен лимит запросов к Mistral AI. Повтор через {retry_after} сек.")
                time.sleep(retry_after)
                
                # Повторный запрос
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
                        "max_tokens": settings.MAX_TOKENS,
                        "response_format": {"type": "json_object"}
                    },
                    timeout=15
                )
            
            response.raise_for_status()
            result = response.json()
            
            content = result["choices"][0]["message"]["content"]
            logger.debug(f"Mistral AI ответ (REST): {content}")
            
            extracted_data = json.loads(content)
            return extracted_data
            
        except json.JSONDecodeError as e:
            logger.error(f"Ошибка парсинга JSON из ответа Mistral AI: {e}")
            raise APIError(f"Ошибка парсинга ответа Mistral AI: {e}")
        except RequestException as e:
            logger.error(f"Ошибка запроса к Mistral AI API: {e}")
            raise APIError(f"Ошибка соединения с Mistral AI: {e}")
        except Exception as e:
            logger.error(f"Непредвиденная ошибка при обращении к Mistral AI API: {e}")
            raise APIError(f"Непредвиденная ошибка при работе с Mistral AI: {e}")

    def _build_extraction_prompt(self, message: str, context: Dict[str, Any]) -> str:
        """
        Формирует промпт для извлечения сущностей.
        """
        return f"""
        # Задача
        Ты - система извлечения информации из сообщений пользователя. Извлеки следующие сущности:

        - date: Дата в формате dd.mm.yyyy (текущий год 2025, если не указан)
        - start_city: Город отправления на русском
        - end_city: Город прибытия на русском
        - mid_city: Список промежуточных городов
        - prefered_transport: Предпочтения транспорта (1 - выбран, 0 - не выбран)
            - train: поезд
            - plane: самолет
            - bus: автобус

        # Текущие данные
        Текущие сущности:
        {json.dumps(context, ensure_ascii=False, indent=2)}

        # Сообщение пользователя:
        {message}

        # Правила
        1. Обнови ТОЛЬКО явно упомянутые в сообщении сущности
        2. Для транспорта: 1 если пользователь выбрал, 0 если явно отказался
        3. Если транспорт не упомянут - оставь текущие значения
        4. Для даты учитывай контекст текущего года
        5. Сокращенные и неформальные названия городов приводи к полной форме и именительному падежу (Например: Питер - Санкт-Петербург, Москоу - Москва)
        # Формат ответа (ТОЛЬКО JSON):
        {{
          "date": "дд.мм.гггг",
          "start_city": "город",
          "end_city": "город",
          "mid_city": ["город1", "город2"],
          "prefered_transport": {{
            "train": 1,
            "plane": 0,
            "bus": 0
          }}
        }}
        """