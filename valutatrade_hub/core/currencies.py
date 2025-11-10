from abc import ABC, abstractmethod
from typing import Dict

from valutatrade_hub.core.constants import (
    CURRENCY_NOT_FOUND_MSG,
    MAX_CURRENCY_CODE_LENGTH,
    MIN_CURRENCY_CODE_LENGTH,
)
from valutatrade_hub.core.exceptions import CurrencyNotFoundError


class Currency(ABC):
    """Абстрактный базовый класс для валют"""
    
    def __init__(self, name: str, code: str):
        self._validate_code(code)
        self._validate_name(name)
        
        self.name = name
        self.code = code.upper()
    
    def _validate_code(self, code: str) -> None:
        """Функция валидации кода валюты"""
        if not code or not isinstance(code, str):
            raise ValueError("Код валюты не может быть пустым")
        
        code_clean = code.strip().upper()
        if (len(code_clean) < MIN_CURRENCY_CODE_LENGTH or 
            len(code_clean) > MAX_CURRENCY_CODE_LENGTH):
            raise ValueError(
                f"Код валюты должен содержать от {MIN_CURRENCY_CODE_LENGTH} "
                f"до {MAX_CURRENCY_CODE_LENGTH} символов"
            )
        
        if ' ' in code_clean:
            raise ValueError("Код валюты не может содержать пробелы")
    
    def _validate_name(self, name: str) -> None:
        """Функция валидации имени валюты"""
        if not name or not isinstance(name, str):
            raise ValueError("Название валюты не может быть пустым")
        
        if not name.strip():
            raise ValueError("Название валюты не может быть пустой строкой")
        
    @abstractmethod
    def get_display_info(self) -> str:
        """Функция возвращает строковое представление для UI/логов"""
        pass
    
    def __str__(self) -> str:
        return self.get_display_info()
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name='{self.name}', code='{self.code}')"
    
class FiatCurrency(Currency):
    """Фиатная валюта"""
    
    def __init__(self, name: str, code: str, issuing_country: str = ""):
        super().__init__(name, code)
        self.issuing_country = issuing_country
        self.currency_type = "fiat"
    
    def get_display_info(self) -> str:
        return f"[FIAT] {self.code} — {self.name}"

class CryptoCurrency(Currency):
    """Криптовалюта"""
    
    def __init__(self, name: str, code: str, algorithm: str = "", 
                 market_cap: float = 0):
        super().__init__(name, code)
        self.algorithm = algorithm
        self.market_cap = market_cap
        self.currency_type = "crypto"
    
    def get_display_info(self) -> str:
        return f"[CRYPTO] {self.code} — {self.name}"


_currency_registry: Dict[str, Currency] = {}

def _initialize_currencies():
    """Инициализация валют с учетом данных из парсера"""
    global _currency_registry
    

    fiat_currencies = [
        FiatCurrency("US Dollar", "USD", "United States"),
        FiatCurrency("Euro", "EUR", "European Union"),
        FiatCurrency("British Pound", "GBP", "United Kingdom"),
        FiatCurrency("Russian Ruble", "RUB", "Russia"),
        FiatCurrency("Japanese Yen", "JPY", "Japan"),
        FiatCurrency("Chinese Yuan", "CNY", "China"),
        FiatCurrency("Canadian Dollar", "CAD", "Canada"),
        FiatCurrency("Australian Dollar", "AUD", "Australia"),
        FiatCurrency("Swiss Franc", "CHF", "Switzerland"),
    ]
    

    crypto_currencies = [
        CryptoCurrency("Bitcoin", "BTC", "SHA-256", 1.1e12),
        CryptoCurrency("Ethereum", "ETH", "Proof-of-Stake", 400e9),
        CryptoCurrency("Solana", "SOL", "Proof-of-History", 60e9),
        CryptoCurrency("Cardano", "ADA", "Ouroboros", 15e9),
        CryptoCurrency("Polkadot", "DOT", 
                       "Nominated Proof-of-Stake", 10e9),
        CryptoCurrency("Dogecoin", "DOGE", "Scrypt", 20e9),
    ]
    

    for currency in fiat_currencies + crypto_currencies:
        _currency_registry[currency.code] = currency

def get_currency(code: str) -> Currency:
    """Фабричный метод для получения валюты по коду"""
    if not _currency_registry:
        _initialize_currencies()
    
    code_upper = code.strip().upper()
    
    if code_upper not in _currency_registry:
        raise CurrencyNotFoundError(CURRENCY_NOT_FOUND_MSG.format(code=code))
    
    return _currency_registry[code_upper]


def get_all_currencies() -> list[Currency]:
    """Получить все доступные валюты"""
    if not _currency_registry:
        _initialize_currencies()
    return list(_currency_registry.values())

def get_currencies_by_type(currency_type: str) -> list[Currency]:
    """Получить валюты по типу (fiat/crypto)"""
    if not _currency_registry:
        _initialize_currencies()
    
    return [currency for currency in _currency_registry.values() 
            if getattr(currency, 'currency_type', None) == currency_type]

_initialize_currencies()