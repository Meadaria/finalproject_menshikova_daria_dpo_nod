from abc import ABC, abstractmethod
from typing import Dict
import requests

from valutatrade_hub.core.exceptions import ApiRequestError


class BaseApiClient(ABC):
    """Изолированая логика работы с каждым внешним сервисом"""
    
    @abstractmethod
    def fetch_rates(self) -> Dict[str, float]:
        """  Получение курсов валют от API   """
        pass


class CoinGeckoClient(BaseApiClient):
    """Клиент для работы с CoinGecko API"""
    
    def __init__(self, crypto_id_map: Dict[str, str], timeout: int = 10):
        self.crypto_id_map = crypto_id_map
        self.timeout = timeout
        self.base_url = "https://api.coingecko.com/api/v3/simple/price"
    
    def fetch_rates(self) -> Dict[str, float]:
        """ Получение курсов криптовалют от CoinGecko  """
        try:
            crypto_ids = ",".join(self.crypto_id_map.values())
            params = {
                'ids': crypto_ids,
                'vs_currencies': 'usd'
            }
            
            response = requests.get(self.base_url, params=params, timeout=self.timeout)
            response.raise_for_status()
            
            data = response.json()
            
            rates = {}
            for crypto_code, crypto_id in self.crypto_id_map.items():
                if crypto_id in data and 'usd' in data[crypto_id]:
                    rate = data[crypto_id]['usd']
                    pair_key = f"{crypto_code}_USD"
                    rates[pair_key] = rate
            
            return rates
            
        except requests.exceptions.RequestException as e:
            error_msg = f"CoinGecko API error: {e}"
            if hasattr(e, 'response') and e.response is not None:
                error_msg += f" (Status: {e.response.status_code})"
            raise ApiRequestError(error_msg)


class ExchangeRateApiClient(BaseApiClient):
    """Клиент для работы с ExchangeRate-API"""
    
    def __init__(self, api_key: str, base_currency: str = "USD", timeout: int = 10):
        self.api_key = api_key
        self.base_currency = base_currency
        self.timeout = timeout
        self.base_url = f"https://v6.exchangerate-api.com/v6/{api_key}/latest/{base_currency}"
    
    def fetch_rates(self) -> Dict[str, float]:
        """ Получение курсов фиатных валют от ExchangeRate-API  """
        try:
            response = requests.get(self.base_url, timeout=self.timeout)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get("result") != "success":
                error_type = data.get("error-type", "unknown_error")
                raise ApiRequestError(f"ExchangeRate-API error: {error_type}")

            base_rates = data.get("rates", {})
            
            rates = {}
            for currency_code, rate in base_rates.items():
                if currency_code != self.base_currency:
                    pair_key = f"{currency_code}_{self.base_currency}"
                    rates[pair_key] = rate
            
            return rates
            
        except requests.exceptions.RequestException as e:
            error_msg = f"ExchangeRate-API error: {e}"
            if hasattr(e, 'response') and e.response is not None:
                status_code = e.response.status_code
                if status_code == 401:
                    error_msg = "Неверный API ключ для ExchangeRate-API"
                elif status_code == 429:
                    error_msg = "Превышен лимит запросов к ExchangeRate-API"
                elif status_code == 403:
                    error_msg = "Доступ к ExchangeRate-API запрещен"
            raise ApiRequestError(error_msg)