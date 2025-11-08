import logging
import time
import threading
from typing import Optional

logger = logging.getLogger(__name__)


class Scheduler:
    """  Планировщик для периодического выполнения обновления курсов валют.  """
    
    def __init__(self, updater, interval_seconds: int = 300):

        self.updater = updater
        self.interval_seconds = interval_seconds
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        logger.info(f"Планировщик инициализирован с интервалом {interval_seconds} секунд")

    def start(self) -> None:
        """Функция запуска планировщика"""
        if self._thread and self._thread.is_alive():
            logger.warning("Планировщик уже запущен")
            return
        
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        logger.info("Планировщик запущен")

    def stop(self) -> None:
        """Функция остановки планировщика"""
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=5)
        logger.info("Планировщик остановлен")

    def _run(self) -> None:
        """Основной цикл выполнения планировщика"""
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
            while wait_time < self.interval_seconds and not self._stop_event.is_set():
                time.sleep(1)
                wait_time += 1

        logger.info("Цикл планировщика завершен")

    def run_once(self) -> bool:

        logger.info("Запуск единоразового обновления")
        try:
            return self.updater.run_update()
        except Exception as e:
            logger.error(f"Ошибка при единоразовом обновлении: {e}")
            return False

    @property
    def is_running(self) -> bool:
        """Функция проверки, работает ли планировщик"""
        return self._thread is not None and self._thread.is_alive()