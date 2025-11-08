import functools
from datetime import datetime
from typing import Any, Callable
from valutatrade_hub.core.session import get_current_user_id
from valutatrade_hub.logging_config import logger 


def log_action(action: str, verbose: bool = False):
    """ Декоратор для логирования доменных операций """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            timestamp = datetime.now().isoformat()
            user_id = get_current_user_id()
            
            try:
                
                logger.info(f"{timestamp} {action} START user_id={user_id}")
                
                result = func(*args, **kwargs)
                
                log_message = f"{timestamp} {action} SUCCESS user_id={user_id}"
                
                if action in ['BUY', 'SELL'] and len(args) >= 2:
                    log_message += f" currency='{args[0]}' amount={args[1]:.4f}"
                
                elif action == 'REGISTER' and len(args) >= 1:
                    log_message += f" username='{args[0]}'"
                
                elif action == 'LOGIN' and len(args) >= 1:
                    log_message += f" username='{args[0]}'"
                
                logger.info(log_message)
                return result
                
            except Exception as e:
                error_message = f"{timestamp} {action} ERROR user_id={user_id} error='{type(e).__name__}: {str(e)}'"
                logger.error(error_message)
                raise
        
        return wrapper
    return decorator