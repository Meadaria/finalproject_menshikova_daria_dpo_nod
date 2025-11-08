class InsufficientFundsError(Exception):
    """Ошибка недостатка средств"""
    def __init__(self, available: float, required: float, code: str):
        self.available = available
        self.required = required
        self.code = code
        message = f"Недостаточно средств: доступно {available} {code}, требуется {required} {code}"
        super().__init__(message)


class CurrencyNotFoundError(Exception):
    """Ошибка неизвестной валюты"""
    def __init__(self, code: str):
        self.code = code
        message = f"Неизвестная валюта '{code}'"
        super().__init__(message)


class ApiRequestError(Exception):
    """Ошибка обращения к внешнему API"""
    def __init__(self, reason: str):
        self.reason = reason
        message = f"Ошибка при обращении к внешнему API: {reason}"
        super().__init__(message)


class StorageError(Exception):
    """Ошибка при работе с хранилищем данных"""
    def __init__(self, reason: str):
        self.reason = reason
        message = f"Ошибка при работе с хранилищем данных: {reason}"
        super().__init__(message)


class ConfigError(Exception):
    """Ошибка конфигурации"""
    def __init__(self, reason: str):
        self.reason = reason
        message = f"Ошибка конфигурации: {reason}"
        super().__init__(message)