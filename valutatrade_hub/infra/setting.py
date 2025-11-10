from pathlib import Path
from typing import Any

import tomli

from valutatrade_hub.infra.constants import (
    CONFIG_SECTION,
    DEFAULT_BASE_CURRENCY,
    DEFAULT_DATA_DIR,
    DEFAULT_LOG_LEVEL,
    DEFAULT_RATES_TTL,
    PYPROJECT_PATH,
)


class SettingsLoader:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_config()
        return cls._instance
    
    def _load_config(self):
        self._config = {
            "data_directory": DEFAULT_DATA_DIR,
            "rates_ttl_seconds": DEFAULT_RATES_TTL,
            "default_base_currency": DEFAULT_BASE_CURRENCY,
            "log_level": DEFAULT_LOG_LEVEL
        }
        
        pyproject_path = Path(PYPROJECT_PATH)
        if pyproject_path.exists():
            try:
                with open(pyproject_path, 'rb') as f:
                    data = tomli.load(f)
                    tool_config = data.get('tool', {}).get(CONFIG_SECTION, {})
                    self._config.update(tool_config)
            except ImportError:
                pass  
    
    def get(self, key: str, default: Any = None) -> Any:
        return self._config.get(key, default)

settings = SettingsLoader()