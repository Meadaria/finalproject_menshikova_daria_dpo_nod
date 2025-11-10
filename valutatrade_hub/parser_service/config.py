import os
from dataclasses import dataclass
from typing import Dict, Tuple

from dotenv import load_dotenv

from valutatrade_hub.core.exceptions import ConfigError
from valutatrade_hub.parser_service.constants import (
    API_KEY_MISSING_MSG,
    CONFIG_VALIDATION_FAILED,
    DEFAULT_REQUEST_TIMEOUT,
    DEFAULT_UPDATE_INTERVAL,
    HISTORY_FILENAME,
    RATES_FILENAME,
)

load_dotenv()

@dataclass(frozen=True)
class ParserConfig:
    """Конфигурация для сервиса парсинга курсов валют."""
    
    # API ключи 
    EXCHANGERATE_API_KEY: str = os.getenv("EXCHANGERATE_API_KEY", "")
    COINGECKO_API_KEY: str = os.getenv("COINGECKO_API_KEY", "")
    
    # Базовые URL API
    COINGECKO_BASE_URL: str = "https://api.coingecko.com/api/v3"
    EXCHANGERATE_API_BASE_URL: str = "https://v6.exchangerate-api.com/v6"
    
    # Списки валют для отслеживания
    BASE_FIAT_CURRENCY: str = "USD"
    FIAT_CURRENCIES: Tuple[str, ...] = (
        "EUR", "GBP", "RUB", "JPY", "CNY", "CAD", "AUD", "CHF"
    )
    CRYPTO_CURRENCIES: Tuple[str, ...] = ("BTC", "ETH", "SOL", "ADA", "DOT", "DOGE")
    
    # Маппинг криптовалют
    CRYPTO_ID_MAP: Dict[str, str] = None
    
    # Таймауты и интервалы
    REQUEST_TIMEOUT: int = DEFAULT_REQUEST_TIMEOUT
    UPDATE_INTERVAL: int = DEFAULT_UPDATE_INTERVAL
    
    # Пути к файлам
    RATES_FILE_PATH: str = f"data/{RATES_FILENAME}"
    HISTORY_FILE_PATH: str = f"data/{HISTORY_FILENAME}"
    
    def __post_init__(self):
        """Инициализация вычисляемых полей после создания объекта."""
        if self.CRYPTO_ID_MAP is None:
            object.__setattr__(self, 'CRYPTO_ID_MAP', {
                "BTC": "bitcoin",
                "ETH": "ethereum",
                "SOL": "solana",
                "ADA": "cardano",
                "DOT": "polkadot",
                "DOGE": "dogecoin"
            })
    
    @property
    def exchangerate_api_url(self) -> str:
        """Полный URL для ExchangeRate-API с подставленным ключом."""
        if not self.EXCHANGERATE_API_KEY:
            raise ValueError(API_KEY_MISSING_MSG.format("ExchangeRate-API"))
        return (f"{self.EXCHANGERATE_API_BASE_URL}/"
                f"{self.EXCHANGERATE_API_KEY}/latest/{self.BASE_FIAT_CURRENCY}")
    
    @property
    def coingecko_price_url(self) -> str:
        """Полный URL для CoinGecko API с параметрами."""
        crypto_ids = ",".join(self.CRYPTO_ID_MAP.values())
        return (f"{self.COINGECKO_BASE_URL}/simple/price?"
                f"ids={crypto_ids}&vs_currencies=usd")
    
    def validate_config(self) -> bool:
        """Проверка валидности конфигурации."""
        if not self.FIAT_CURRENCIES:
            raise ConfigError(CONFIG_VALIDATION_FAILED.format(
                "Список FIAT_CURRENCIES не может быть пустым"
            ))
        
        if not self.CRYPTO_CURRENCIES:
            raise ConfigError(CONFIG_VALIDATION_FAILED.format(
                "Список CRYPTO_CURRENCIES не может быть пустым"
            ))
        
        if not self.CRYPTO_ID_MAP:
            raise ConfigError(CONFIG_VALIDATION_FAILED.format(
                "CRYPTO_ID_MAP не может быть пустым"
            ))

        for crypto_code in self.CRYPTO_CURRENCIES:
            if crypto_code not in self.CRYPTO_ID_MAP:
                raise ConfigError(CONFIG_VALIDATION_FAILED.format(
                    f"Криптовалюта {crypto_code} отсутствует в CRYPTO_ID_MAP"
                ))
        
        return True

parser_config = ParserConfig()