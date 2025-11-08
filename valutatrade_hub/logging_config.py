import logging
import logging.handlers
from pathlib import Path
from valutatrade_hub.infra.setting import settings


def _setup_logging():
    """Настройка системы логирования"""
    log_file = settings.get("log_file", "logs/valutatrade.log")
    Path(log_file).parent.mkdir(exist_ok=True)
    
    formatter = logging.Formatter(
        fmt='%(levelname)s %(asctime)s %(message)s',
        datefmt='%Y-%m-%dT%H:%M:%S'
    )
    
    file_handler = logging.handlers.RotatingFileHandler(
        filename=log_file,
        maxBytes=10*1024*1024,  
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    
    logger = logging.getLogger('valutatrade')
    logger.setLevel(settings.get("log_level", "INFO"))
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger


logger = _setup_logging()