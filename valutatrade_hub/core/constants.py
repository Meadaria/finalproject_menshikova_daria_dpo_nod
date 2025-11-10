"""
Общие константы приложения
"""

# Настройки безопасности
MIN_PASSWORD_LENGTH = 4
SALT_LENGTH_BYTES = 16
PASSWORD_HASH_ALGORITHM = "sha256"

# Настройки файлов
DEFAULT_ENCODING = "utf-8"

# Финансовые настройки
DEFAULT_BASE_CURRENCY = "USD"
INITIAL_BALANCE = 0.0
RATES_CACHE_TTL_HOURS = 1

# Валидация
MAX_CURRENCY_CODE_LENGTH = 5
MIN_CURRENCY_CODE_LENGTH = 2

# Сообщения об ошибках
INSUFFICIENT_FUNDS_MSG = "Недостаточно средств: доступно"
" {available} {code}, требуется {required} {code}"
CURRENCY_NOT_FOUND_MSG = "Валюта с кодом '{code}' не найдена"

# Курсы валют по умолчанию
DEFAULT_EXCHANGE_RATES = {
    "USD": 1.0,
    "EUR": 0.85,
    "GBP": 0.75,
    "JPY": 110.0,
    "BTC": 45000.0,
    "ETH": 3000.0,
    "RUB": 0.011
}

# Сообщения об ошибках Wallet
BALANCE_NEGATIVE_ERROR = "Баланс не может быть отрицательным"
BALANCE_TYPE_ERROR = "Баланс должен быть числом (int или float)"
AMOUNT_POSITIVE_ERROR = "Сумма операции должна быть положительным числом"
AMOUNT_TYPE_ERROR = "Сумма операции должна быть числом (int или float)"
CURRENCY_CODE_EMPTY_ERROR = "Код валюты не может быть пустым"

# Сообщения об ошибках Portfolio
CURRENCY_NOT_IN_PORTFOLIO = "Кошелек для валюты '{}' не найден"
CURRENCY_ALREADY_EXISTS = "Кошелек для валюты '{}' уже существует в портфеле"
EXCHANGE_RATE_NOT_FOUND = "Курс для валюты '{}' не найден"