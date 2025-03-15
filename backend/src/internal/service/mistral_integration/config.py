"""
Модуль конфигурации для работы с Mistral AI API.
"""

import os
from pydantic import BaseSettings


class MistralAISettings(BaseSettings):
    """
    Настройки для работы с Mistral AI API.
    Значения загружаются из переменных окружения.
    """
    API_KEY: str = os.getenv("MISTRAL_API_KEY", "")
    API_URL: str = os.getenv("MISTRAL_API_URL", "https://api.mistral.ai/v1/chat/completions")
    MODEL_NAME: str = os.getenv("MISTRAL_MODEL_NAME", "mistral-large-latest")
    TEMPERATURE: float = float(os.getenv("MISTRAL_TEMPERATURE", "0.1"))
    MAX_TOKENS: int = int(os.getenv("MISTRAL_MAX_TOKENS", "500"))
    
    def is_configured(self) -> bool:
        """Проверяет, что API ключ задан и можно использовать API."""
        return bool(self.API_KEY)


# Синглтон настроек
settings = MistralAISettings() 