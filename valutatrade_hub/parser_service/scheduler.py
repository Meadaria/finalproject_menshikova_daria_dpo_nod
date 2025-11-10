import logging
import threading
import time
from typing import Optional

from valutatrade_hub.parser_service.constants import POLLING_INTERVAL, SHUTDOWN_TIMEOUT

logger = logging.getLogger(__name__)


class Scheduler:
    """Планировщик для периодического выполнения обновления курсов валют."""
    
    def __init__(self, updater, interval_seconds: int):
        self.updater = updater
        self.interval_seconds = interval_seconds
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        logger.info(f"Планировщик инициализирован с интервалом "
                   f"{self.interval_seconds} секунд")

    def start(self) -> None:
        """Запуск планировщика в отдельном потоке."""
        if self._thread and self._thread.is_alive():
            logger.warning("Планировщик уже запущен")
            return
        
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        logger.info("Планировщик запущен")

    def stop(self) -> None:
        """Остановка планировщика и ожидание завершения потока."""
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=SHUTDOWN_TIMEOUT)
        logger.info("Планировщик остановлен")

    def _run(self) -> None:
        """Основной цикл выполнения планировщика."""
        logger.info("Цикл планировщика начат")
        
        while not self._stop_event.is_set():
            try:
                logger.info("Запуск запланированного обновления курсов")
                success = self.updater.run_update()
                
                if success:
                    logger.info("Запланированное обновление завершено успешно")
                else:
                    logger.error("Запланированное обновление завершено с ошибками")
                    
            except Exception as e:
                logger.error(f"Критическая ошибка в планировщике: {e}")
            
            wait_time = 0
            while (wait_time < self.interval_seconds and 
                   not self._stop_event.is_set()):
                time.sleep(POLLING_INTERVAL)
                wait_time += POLLING_INTERVAL

        logger.info("Цикл планировщика завершен")

    def run_once(self) -> bool:
        """Выполнение единоразового обновления курсов."""
        logger.info("Запуск единоразового обновления")
        try:
            return self.updater.run_update()
        except Exception as e:
            logger.error(f"Ошибка при единоразовом обновлении: {e}")
            return False

    @property
    def is_running(self) -> bool:
        """Проверка, работает ли планировщик."""
        return self._thread is not None and self._thread.is_alive()