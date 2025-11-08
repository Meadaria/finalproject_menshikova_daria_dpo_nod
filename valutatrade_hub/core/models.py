from datetime import datetime
import hashlib
import secrets

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
        return (f"User ID: {self._user_id}\n"
                f"Username: {self._username}\n"
                f"Registration Date: {self._registration_date.strftime('%Y-%m-%d %H:%M:%S')}")
    
    def change_password(self, new_password: str) -> None:
        """Функция изменяет пароль пользователя, с хешированием нового пароля."""
        if not new_password or len(new_password) < 4:
            raise ValueError("Пароль должен быть не короче 4 символов")
        
        self._salt = secrets.token_hex(16)
        self._hashed_password = hashlib.sha256((new_password + self._salt).encode()).hexdigest()

    def verify_password(self, password: str) -> bool:
        """Функция проверки введённого пароля на совпадение."""
        hashed_input = hashlib.sha256((password + self._salt).encode()).hexdigest()
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
        self._balance =  float(balance)

    @property
    def balance(self) -> float:
        return self._balance
    
    @balance.setter
    def balance(self, value: float) -> None:
        value = float(value)
        if value < 0 or not isinstance(value, float):
            raise ValueError("Баланс не может иметь отрицательные значения и некорректные типы данных")
        self._balance = value

    @property
    def currency_code(self) -> str:
        return self._currency_code

    @currency_code.setter
    def currency_code(self, value: str) -> None:
        self._currency_code = self._validate_currency_code(value)

    def _validate_currency_code(self, currency_code: str) -> str:
        """Функция валидирует и нормализует код валюты"""
        if not currency_code or not isinstance(currency_code, str):
            raise ValueError("Код валюты не может быть пустым")
        
        normalized_code = currency_code.strip().upper()
        
        if not normalized_code:
            raise ValueError("Код валюты не может быть пустым")
        
        return normalized_code

    def deposit(self, amount: float):
        """Функция пополнения баланса"""
        if amount < 0:
            raise ValueError("Значение не может иметь отрицательные значения")
        else:
            self._balance += amount
        return self._balance
    
    def withdraw(self, amount: float):
       """Функция снятия средств"""
       if amount > self._balance or amount < 0:
            raise InsufficientFundsError(
                available=self.balance,
                required=amount,
                code=self.currency_code
            )
       else:
        self._balance -= amount
        return self._balance
       
    def get_balance_info(self):
        """Функция вывода информации о текущем балансе"""

        return (f"Валюта: {self._currency_code}\n"
                f"Баланс: {self._balance:.8f}") 
    
    def to_dict(self) -> dict:
        """Функция преобразует объект Wallet в словарь для JSON."""
        return {
            "currency_code": self._currency_code,
            "balance": self._balance
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Wallet':
        """Функция создает объект Wallet из словаря."""
        return cls(
            currency_code=data["currency_code"],
            balance=data["balance"]
        )

    def __str__(self) -> str:
        return f"Wallet({self._currency_code}: {self._balance})"
    

class Portfolio:
    """"Eправление всеми кошельками одного пользователя"""

    def __init__(self, user_id: int, wallets: dict[str, Wallet] = None):
        self._user_id = user_id
        self._wallets = wallets or {} 

        self._exchange_rates = {
            "USD": 1.0,
            "EUR": 1.1,    # 1 EUR = 1.1 USD
            "BTC": 50000.0, # 1 BTC = 50000 USD
            "ETH": 3000.0,  # 1 ETH = 3000 USD
            "RUB": 0.011    # 1 RUB = 0.011 USD
        }

    @property
    def user_id(self) -> int:
        return self._user_id
    
    @property
    def wallets(self) -> dict[str, Wallet]:
        return self._wallets.copy()
    
    def add_currency(self, currency_code: str, initial_balance: float = 0.0) -> None:
        """Функция добовления нового кошелька в портфель (если его ещё нет)"""
        if currency_code in self._wallets:
            raise ValueError(f"Кошелек для валюты {currency_code} уже существует в портфеле")
        self._wallets[currency_code] = Wallet(currency_code, initial_balance)
    
    def get_wallet(self, currency_code: str) -> Wallet:
        """Функция возвращает объект Wallet по коду валюты"""
        if currency_code not in self._wallets:
            raise ValueError(f"Кошелек для валюты {currency_code} не найден")
        return self._wallets[currency_code]
    
    def get_total_value(self, base_currency: str = 'USD') -> float:
        """Функция возвращает общую стоимость всех валют пользователя в указанной базовой валюте"""
        if base_currency not in self._exchange_rates:
            raise ValueError(f"Курс для базовой валюты {base_currency} не найден")
        
        total_value = 0.0
        
        for currency_code, wallet in self._wallets.items():
            if currency_code not in self._exchange_rates:
                raise ValueError(f"Курс для валюты {currency_code} не найден")
            
            if currency_code == base_currency:
                total_value += wallet.balance
            else:
                usd_value = wallet.balance * self._exchange_rates[currency_code]
                if base_currency != "USD":
                    usd_to_base = 1 / self._exchange_rates[base_currency]
                    total_value += usd_value * usd_to_base
                else:
                    total_value += usd_value
        
        return total_value 
    
    def to_dict(self) -> dict:
        """Функция преобразует объект Portfolio в словарь для JSON."""
        wallets_dict = {}
        for currency_code, wallet in self._wallets.items():
            wallets_dict[currency_code] = {"balance": wallet.balance}
        
        return {
            "user_id": self._user_id,
            "wallets": wallets_dict
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Portfolio':
        """Функция создает объект Portfolio из словаря."""
        wallets = {}
        for currency_code, wallet_data in data["wallets"].items():
            wallets[currency_code] = Wallet(currency_code, wallet_data["balance"])
        
        return cls(
            user_id=data["user_id"],
            wallets=wallets
        )

    def __str__(self) -> str:
        return f"Portfolio(user_id={self._user_id}, wallets={list(self._wallets.keys())})"
    

    
    


    


    

