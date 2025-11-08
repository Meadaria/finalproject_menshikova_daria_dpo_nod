import os
from dataclasses import dataclass
from typing import Dict, Tuple
from dotenv import load_dotenv

from valutatrade_hub.core.exceptions import ConfigError

load_dotenv()

@dataclass(frozen=True)
class ParserConfig:
    """Конфигурация для сервиса парсинга курсов валют. """
    
    # API ключи 
    EXCHANGERATE_API_KEY: str = os.getenv("EXCHANGERATE_API_KEY", "")
    COINGECKO_API_KEY: str = os.getenv("COINGECKO_API_KEY", "")
    
    # Базовые URL API
    COINGECKO_BASE_URL: str = "https://api.coingecko.com/api/v3"
    EXCHANGERATE_API_BASE_URL: str = "https://v6.exchangerate-api.com/v6"
    
    # Списки валют для отслеживания
    BASE_FIAT_CURRENCY: str = "USD"
    FIAT_CURRENCIES: Tuple[str, ...] = ("EUR", "GBP", "RUB", "JPY", "CNY", "CAD", "AUD", "CHF")
    CRYPTO_CURRENCIES: Tuple[str, ...] = ("BTC", "ETH", "SOL", "ADA", "DOT", "DOGE")
    
    
    CRYPTO_ID_MAP: Dict[str, str] = None
    

    REQUEST_TIMEOUT: int = 10
    

    RATES_FILE_PATH: str = "data/rates.json"
    HISTORY_FILE_PATH: str = "data/exchange_rates.json"
    
    def __post_init__(self):
        """Функция инициализации вычисляемых полей после создания объекта"""
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
        """Полный URL для ExchangeRate-API с подставленным ключом"""
        if not self.EXCHANGERATE_API_KEY:
            raise ValueError("EXCHANGERATE_API_KEY не установлен")
        return f"{self.EXCHANGERATE_API_BASE_URL}/{self.EXCHANGERATE_API_KEY}/latest/{self.BASE_FIAT_CURRENCY}"
    
    @property
    def coingecko_price_url(self) -> str:
        """Полный URL для CoinGecko API с параметрами"""
        crypto_ids = ",".join(self.CRYPTO_ID_MAP.values())
        return f"{self.COINGECKO_BASE_URL}/simple/price?ids={crypto_ids}&vs_currencies=usd"
    
    def validate_config(self) -> bool:
        """Проверка валидности конфигурации."""
        if not self.FIAT_CURRENCIES:
            raise ConfigError("Список FIAT_CURRENCIES не может быть пустым")
        
        if not self.CRYPTO_CURRENCIES:
            raise ConfigError("Список CRYPTO_CURRENCIES не может быть пустым")
        
        if not self.CRYPTO_ID_MAP:
            raise ConfigError("CRYPTO_ID_MAP не может быть пустым")

        for crypto_code in self.CRYPTO_CURRENCIES:
            if crypto_code not in self.CRYPTO_ID_MAP:
                raise ConfigError(f"Криптовалюта {crypto_code} отсутствует в CRYPTO_ID_MAP")
        
        return True


parser_config = ParserConfig()