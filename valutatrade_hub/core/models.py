import hashlib
import secrets
from datetime import datetime

from valutatrade_hub.core.constants import (
    CURRENCY_ALREADY_EXISTS,
    CURRENCY_NOT_IN_PORTFOLIO,
    DEFAULT_EXCHANGE_RATES,
    MIN_PASSWORD_LENGTH,
    SALT_LENGTH_BYTES,
)
from valutatrade_hub.core.exceptions import InsufficientFundsError


class User:
    """Класс, представляющий пользователя системы."""
    
    def __init__(self, user_id: int, username: str, hashed_password: str, salt: str, 
                 registration_date: datetime = None):
        self._user_id = user_id
        self._username = username
        self._hashed_password = hashed_password
        self._salt = salt
        self._registration_date = registration_date or datetime.now()
    
    @property
    def user_id(self) -> int:
        return self._user_id

    @property   
    def username(self) -> str:
        return self._username
    
    @property
    def hashed_password(self) -> str:
        return self._hashed_password
    
    @property
    def salt(self) -> str:
        return self._salt
    
    @property
    def registration_date(self) -> datetime:
        return self._registration_date
    
    @username.setter
    def username(self, value: str) -> None:
        if not value or not isinstance(value, str):
            raise ValueError("Имя не должно быть пустым")
        self._username = value

    @hashed_password.setter
    def hashed_password(self, value) -> None:
        if not value or len(value) < 4:  
            raise ValueError("Пароль должен быть не короче 4 символов")
        self._hashed_password = value 
    
    def get_user_info(self) -> str:
        """Функция выводит информацию о пользователе"""
        date_str = self._registration_date.strftime('%Y-%m-%d %H:%M:%S')
        return (f"User ID: {self._user_id}\n"
                f"Username: {self._username}\n"
                f"Registration Date: {date_str}")
    
    def change_password(self, new_password: str) -> None:
        """Функция изменяет пароль пользователя, с хешированием нового пароля."""
        if not new_password or len(new_password) < MIN_PASSWORD_LENGTH:
            raise ValueError(
                f"Пароль должен быть не короче {MIN_PASSWORD_LENGTH} символов"
            )
        
        self._salt = secrets.token_hex(SALT_LENGTH_BYTES)
        password_salt = (new_password + self._salt).encode()
        self._hashed_password = hashlib.sha256(password_salt).hexdigest()

    def verify_password(self, password: str) -> bool:
        """Функция проверки введённого пароля на совпадение."""
        password_salt = (password + self._salt).encode()
        hashed_input = hashlib.sha256(password_salt).hexdigest()
        return hashed_input == self._hashed_password

    def to_dict(self) -> dict:
        """Функция преобразует объект User в словарь для JSON."""
        return {
            "user_id": self._user_id,
            "username": self._username,
            "hashed_password": self._hashed_password,
            "salt": self._salt,
            "registration_date": self._registration_date.isoformat()
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'User':
        """Функция создает объект User из словаря."""
        return cls(
            user_id=data["user_id"],
            username=data["username"],
            hashed_password=data["hashed_password"],
            salt=data["salt"],
            registration_date=datetime.fromisoformat(data["registration_date"])
        )
   

class Wallet:
    """Кошелёк пользователя для одной конкретной валюты"""

    def __init__(self, currency_code: str, balance: float = 0.0):
        self._currency_code = self._validate_currency_code(currency_code)
        self._balance = self._validate_balance(balance)  # Используем валидатор

    @property
    def balance(self) -> float:
        return self._balance
    
    @balance.setter
    def balance(self, value: float) -> None:
        self._balance = self._validate_balance(value)

    @property
    def currency_code(self) -> str:
        return self._currency_code

    @currency_code.setter
    def currency_code(self, value: str) -> None:
        self._currency_code = self._validate_currency_code(value)

    def _validate_currency_code(self, currency_code: str) -> str:
        """Валидация и нормализация кода валюты"""
        if not currency_code or not isinstance(currency_code, str):
            raise ValueError("Код валюты не может быть пустым")
        
        normalized_code = currency_code.strip().upper()
        
        if not normalized_code:
            raise ValueError("Код валюты не может быть пустой строкой")
        
        return normalized_code

    def _validate_balance(self, balance: float) -> float:
        """Валидация значения баланса"""
        try:
            balance_float = float(balance)
        except (TypeError, ValueError):
            raise ValueError("Баланс должен быть числом (int или float)")
        
        if balance_float < 0:
            raise ValueError("Баланс не может быть отрицательным")
        
        return balance_float

    def _validate_amount(self, amount: float) -> float:
        """Валидация суммы для операций"""
        try:
            amount_float = float(amount)
        except (TypeError, ValueError):
            raise ValueError("Сумма операции должна быть числом (int или float)")
        
        if amount_float <= 0:
            raise ValueError("Сумма операции должна быть положительным числом")
        
        return amount_float

    def deposit(self, amount: float) -> float:
        """Пополнение баланса с валидацией суммы"""
        validated_amount = self._validate_amount(amount)
        self._balance += validated_amount
        return self._balance
    
    def withdraw(self, amount: float) -> float:
        """Снятие средств с проверкой достаточности баланса"""
        validated_amount = self._validate_amount(amount)
        
        if validated_amount > self._balance:
            raise InsufficientFundsError(
                available=self.balance,
                required=validated_amount,
                code=self.currency_code
            )
        
        self._balance -= validated_amount
        return self._balance
       
    def get_balance_info(self) -> str:
        """Информация о текущем балансе в читаемом формате"""
        return (f"Валюта: {self._currency_code}\n"
                f"Баланс: {self._balance:.8f}") 
    
    def to_dict(self) -> dict:
        """Сериализация в словарь для JSON"""
        return {
            "currency_code": self._currency_code,
            "balance": self._balance
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Wallet':
        """Создание объекта из словаря"""
        return cls(
            currency_code=data["currency_code"],
            balance=data["balance"]
        )

    def __str__(self) -> str:
        return f"Wallet({self._currency_code}: {self._balance})"


class Portfolio:
    """Управление всеми кошельками одного пользователя"""

    def __init__(self, user_id: int, wallets: dict[str, Wallet] = None):
        self._user_id = user_id
        self._wallets = wallets or {}
        self._default_rates = DEFAULT_EXCHANGE_RATES.copy()

    @property
    def user_id(self) -> int:
        return self._user_id
    
    @property
    def wallets(self) -> dict[str, Wallet]:
        return self._wallets.copy()
    
    def add_currency(self, currency_code: str, initial_balance: float = 0.0) -> None:
        """Добавление нового кошелька в портфель"""
        if currency_code in self._wallets:
            raise ValueError(CURRENCY_ALREADY_EXISTS.format(currency_code))
        
        self._wallets[currency_code] = Wallet(currency_code, initial_balance)
    
    def get_wallet(self, currency_code: str) -> Wallet:
        """Получение кошелька по коду валюты"""
        if currency_code not in self._wallets:
            raise ValueError(CURRENCY_NOT_IN_PORTFOLIO.format(currency_code))
        return self._wallets[currency_code]
    
    def has_currency(self, currency_code: str) -> bool:
        """Проверка наличия валюты в портфеле"""
        return currency_code in self._wallets

    def get_exchange_rate(self, from_currency: str, to_currency: str,
                           rates: dict = None) -> float:
        """Получает курс обмена между валютами с 
        использованием переданных курсов из парсера"""
    
        if from_currency == to_currency:
            return 1.0
        
        if rates:
            pair_key = f"{from_currency}_{to_currency}"
            if pair_key in rates:
                return rates[pair_key]

            reverse_pair_key = f"{to_currency}_{from_currency}"
            if reverse_pair_key in rates:
                return 1 / rates[reverse_pair_key]

            if from_currency != "USD" and to_currency != "USD":
                from_to_usd = self.get_exchange_rate(from_currency, "USD", rates)
                usd_to_to = self.get_exchange_rate("USD", to_currency, rates)
                
                if from_to_usd and usd_to_to:
                    return from_to_usd * usd_to_to

        static_rates = {
            "BTC_USD": 106194.0,
            "ETH_USD": 3000.0,
            "EUR_USD": 0.85,
            "USD_EUR": 1.18,
            "USD_BTC": 0.00000942,
            "USD_ETH": 0.000333,
            "EUR_BTC": 0.000008,
            "BTC_EUR": 125000.0,
        }

        pair_key = f"{from_currency}_{to_currency}"
        if pair_key in static_rates:
            return static_rates[pair_key]
        
        reverse_pair_key = f"{to_currency}_{from_currency}"
        if reverse_pair_key in static_rates:
            return 1 / static_rates[reverse_pair_key]

        if from_currency != "USD" and to_currency != "USD":
            from_to_usd = self.get_exchange_rate(from_currency, "USD", None)  
            usd_to_to = self.get_exchange_rate("USD", to_currency, None)
            
            if from_to_usd and usd_to_to:
                return from_to_usd * usd_to_to

        return None
    
    def get_total_value(self, base_currency: str = "USD",
                         rates: dict = None) -> float:
        """Функция рассчета общий стоимости портфеля"""
        total = 0.0
        
        for currency_code, wallet in self.wallets.items():
            if currency_code == base_currency:
                total += wallet.balance
            else:
                rate = self.get_exchange_rate(currency_code, base_currency, rates)
                if rate is not None:
                    total += wallet.balance * rate
                else:
                    print(f"Предупреждение: курс для {currency_code} не найден")
        
        return total

    def get_portfolio_summary(self, rates: dict = None) -> dict:
        """Функция возвращает сводку портфеля"""
        summary = {"wallets": {}}
        
        for currency_code, wallet in self.wallets.items():
            rate_to_usd = self.get_exchange_rate(currency_code, "USD", rates)
            value_usd = wallet.balance * rate_to_usd if rate_to_usd else 0
            
            summary["wallets"][currency_code] = {
                "balance": wallet.balance,
                "rate_to_usd": rate_to_usd,
                "value_usd": value_usd
            }
        
        return summary
    
    def to_dict(self) -> dict:
        """Сериализация в словарь для JSON"""
        wallets_dict = {}
        for currency_code, wallet in self._wallets.items():
            wallets_dict[currency_code] = wallet.to_dict()
        
        return {
            "user_id": self._user_id,
            "wallets": wallets_dict
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Portfolio':
        """Создание объекта из словаря"""
        wallets = {}
        for currency_code, wallet_data in data["wallets"].items():
            wallets[currency_code] = Wallet.from_dict({
                "currency_code": currency_code,
                "balance": wallet_data["balance"]
            })
        
        return cls(
            user_id=data["user_id"],
            wallets=wallets
        )

    def __str__(self) -> str:
        wallet_keys = list(self._wallets.keys())
        return f"Portfolio(user_id={self._user_id}, wallets={wallet_keys})"
    
    


    


    

