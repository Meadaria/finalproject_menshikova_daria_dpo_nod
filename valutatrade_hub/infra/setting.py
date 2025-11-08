from pathlib import Path
from typing import Any
import tomli


class SettingsLoader:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_config()
        return cls._instance
    
    def _load_config(self):
        self._config = {
            "data_directory": "data/",
            "rates_ttl_seconds": 300,
            "default_base_currency": "USD",
            "log_level": "INFO"
        }
        
        pyproject_path = Path("pyproject.toml")
        if pyproject_path.exists():
            try:
                with open(pyproject_path, 'rb') as f:
                    data = tomli.load(f)
                    tool_config = data.get('tool', {}).get('valutatrade', {})
                    self._config.update(tool_config)
            except ImportError:
                pass  
    
    def get(self, key: str, default: Any = None) -> Any:
        return self._config.get(key, default)

settings = SettingsLoader()