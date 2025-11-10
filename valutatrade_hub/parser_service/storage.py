import json
import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict

from valutatrade_hub.core.exceptions import StorageError

logger = logging.getLogger(__name__)


class BaseStorage(ABC):
    """Абстрактный базовый класс для хранилищ данных"""
    
    @abstractmethod
    def save(self, data: Dict[str, Any]) -> None:
        """Сохранить данные в хранилище"""
        pass
    
    @abstractmethod
    def load(self) -> Dict[str, Any]:
        """Загрузить данные из хранилища"""
        pass


class JsonFileStorage(BaseStorage):
    """Реализация хранилища в формате JSON файла"""
    
    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        logger.info(f"Инициализировано JSON хранилище: {self.file_path}")

    def save(self, data: Dict[str, Any]) -> None:
        """Атомарное сохранение данных через временный файл"""
        temp_path = None
        try:
            self.file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Создание временного файла
            temp_path = self.file_path.with_suffix('.tmp')
            
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            # Атомарная замена
            temp_path.replace(self.file_path)
            
            logger.debug(f"Данные успешно сохранены в {self.file_path}")
            
        except (IOError, OSError, TypeError) as e:
            # Удаление временного файла при ошибке
            if temp_path and temp_path.exists():
                try:
                    temp_path.unlink()
                except OSError:
                    pass
            error_msg = f"Ошибка сохранения в {self.file_path}: {e}"
            logger.error(error_msg)
            raise StorageError(error_msg) from e

    def load(self) -> Dict[str, Any]:
        """Загрузить данные из JSON файла"""
        try:
            if not self.file_path.exists():
                logger.warning(f"Файл {self.file_path} не существует, "
                              f"возвращаем пустые данные")
                return {}
            
            with open(self.file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            logger.debug(f"Данные успешно загружены из {self.file_path}")
            return data
            
        except (IOError, OSError, json.JSONDecodeError) as e:
            error_msg = f"Ошибка загрузки из {self.file_path}: {e}"
            logger.error(error_msg)
            raise StorageError(error_msg) from e

    def exists(self) -> bool:
        """Проверить существование файла хранилища"""
        return self.file_path.exists()