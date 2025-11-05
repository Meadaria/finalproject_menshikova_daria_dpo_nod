# Глобальная переменная для текущей сессии
_current_user_id: int = None

def get_current_user_id() -> int:
    return _current_user_id

def set_current_user_id(user_id: int) -> None:
    global _current_user_id
    _current_user_id = user_id

def logout() -> None:
    global _current_user_id
    _current_user_id = None