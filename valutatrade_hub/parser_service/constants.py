"""
Константы для Parser Service
"""

# Настройки запросов
DEFAULT_REQUEST_TIMEOUT = 10
MAX_REQUEST_TIMEOUT = 30
RETRY_ATTEMPTS = 3

# Настройки планировщика
DEFAULT_UPDATE_INTERVAL = 300  # 5 минут
MIN_UPDATE_INTERVAL = 60       # 1 минута
SHUTDOWN_TIMEOUT = 5           # секунд на завершение потока
POLLING_INTERVAL = 1           # секунда между проверками остановки

# Настройки файлов
RATES_FILENAME = "rates.json"
HISTORY_FILENAME = "exchange_rates.json"

# Логирование
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# API лимиты
COINGECKO_RATE_LIMIT_DELAY = 1.0  # секунда между запросами
MAX_RATES_PER_REQUEST = 100

# Сообщения об ошибках
API_KEY_MISSING_MSG = "API ключ не установлен для {}"
CONFIG_VALIDATION_FAILED = "Ошибка валидации конфигурации: {}"

# Команды CLI
COMMAND_UPDATE = "update"
COMMAND_SCHEDULE = "schedule"
SOURCE_COINGECKO = "coingecko"
SOURCE_EXCHANGERATE = "exchangerate"