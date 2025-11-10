import logging
import logging.handlers
from pathlib import Path

from valutatrade_hub.infra.constants import (
    BACKUP_COUNT,
    DATE_FORMAT,
    DEFAULT_ENCODING,
    DEFAULT_LOG_FILE,
    DEFAULT_LOG_LEVEL,
    LOG_FORMAT,
    MAX_LOG_SIZE_BYTES,
)
from valutatrade_hub.infra.setting import settings


def _setup_logging():
    """Настройка системы логирования."""
    log_file = settings.get("log_file", DEFAULT_LOG_FILE)
    Path(log_file).parent.mkdir(exist_ok=True)
    
    formatter = logging.Formatter(
        fmt=LOG_FORMAT,
        datefmt=DATE_FORMAT
    )
    
    file_handler = logging.handlers.RotatingFileHandler(
        filename=log_file,
        maxBytes=MAX_LOG_SIZE_BYTES,
        backupCount=BACKUP_COUNT,
        encoding=DEFAULT_ENCODING
    )
    file_handler.setFormatter(formatter)
    
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    
    logger = logging.getLogger('valutatrade')
    logger.setLevel(settings.get("log_level", DEFAULT_LOG_LEVEL))
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger


logger = _setup_logging()