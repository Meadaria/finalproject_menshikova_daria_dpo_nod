"""
Константы для инфраструктурного слоя
"""

# Настройки по умолчанию для SettingsLoader
DEFAULT_DATA_DIR = "data/"
DEFAULT_RATES_TTL = 300
DEFAULT_BASE_CURRENCY = "USD"
DEFAULT_LOG_LEVEL = "INFO"

# Настройки файлов
PYPROJECT_PATH = "pyproject.toml"
CONFIG_SECTION = "valutatrade"
DEFAULT_ENCODING = "utf-8"

# Настройки логирования
DEFAULT_LOG_FILE = "logs/valutatrade.log"
LOG_FORMAT = '%(levelname)s %(asctime)s %(message)s'
DATE_FORMAT = '%Y-%m-%dT%H:%M:%S'

# Настройки RotatingFileHandler
MAX_LOG_SIZE_BYTES = 10 * 1024 * 1024  # 10MB
BACKUP_COUNT = 5