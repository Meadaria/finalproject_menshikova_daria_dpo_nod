import functools
from datetime import datetime
from typing import Any, Callable

from valutatrade_hub.core.session import get_current_user_id
from valutatrade_hub.logging_config import logger

# Константы для индексов аргументов
CURRENCY_ARG_INDEX = 0
AMOUNT_ARG_INDEX = 1
USERNAME_ARG_INDEX = 0

# Константы для минимального количества аргументов
MIN_BUY_SELL_ARGS = 2
MIN_USERNAME_ARGS = 1

# Форматы чисел
AMOUNT_FORMAT = ".4f"


def log_action(action: str, verbose: bool = False):
    """Декоратор для логирования доменных операций."""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            timestamp = datetime.now().isoformat()
            user_id = get_current_user_id()
            
            try:
                logger.info(f"{timestamp} {action} START user_id={user_id}")
                
                result = func(*args, **kwargs)
                
                log_message = f"{timestamp} {action} SUCCESS user_id={user_id}"
                
                # Логирование дополнительной информации в зависимости от действия
                if action in ['BUY', 'SELL'] and len(args) >= MIN_BUY_SELL_ARGS:
                    currency = args[CURRENCY_ARG_INDEX]
                    amount = args[AMOUNT_ARG_INDEX]
                    log_message += f" currency='{currency}'"
                    f"amount={amount:{AMOUNT_FORMAT}}"
                
                elif action == 'REGISTER' and len(args) >= MIN_USERNAME_ARGS:
                    username = args[USERNAME_ARG_INDEX]
                    log_message += f" username='{username}'"
                
                elif action == 'LOGIN' and len(args) >= MIN_USERNAME_ARGS:
                    username = args[USERNAME_ARG_INDEX]
                    log_message += f" username='{username}'"
                
                logger.info(log_message)
                return result
                
            except Exception as e:
                error_message = (f"{timestamp} {action} ERROR user_id={user_id} "
                                f"error='{type(e).__name__}: {str(e)}'")
                logger.error(error_message)
                raise
        
        return wrapper
    return decorator