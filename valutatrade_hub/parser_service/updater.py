import logging
from typing import Dict, List
from datetime import datetime, timezone

from valutatrade_hub.core.exceptions import ApiRequestError
from valutatrade_hub.parser_service.api_clients import BaseApiClient
from valutatrade_hub.parser_service.storage import BaseStorage


logger = logging.getLogger(__name__)


class RatesUpdater:
    """   Координатор процесса обновления курсов валют. """
    
    def __init__(self, api_clients: List[BaseApiClient], storage: BaseStorage):
        
        self.api_clients = api_clients
        self.storage = storage
        logger.info(f"RatesUpdater инициализирован с {len(api_clients)} клиентами")

    def run_update(self) -> bool:
        """ Основной метод выполнения обновления курсов. """
        logger.info("Запуск обновления курсов валют")
        
        all_rates = {}
        successful_clients = 0
        

        for i, client in enumerate(self.api_clients):
            client_name = client.__class__.__name__
            logger.info(f"Опрос клиента {i+1}/{len(self.api_clients)}: {client_name}")
            
            try:
                rates = client.fetch_rates()
                all_rates.update(rates)
                successful_clients += 1
                logger.info(f"Клиент {client_name} успешно предоставил {len(rates)} курсов")
                
            except ApiRequestError as e:
                logger.error(f"Ошибка при опросе {client_name}: {e}")
                continue
            except Exception as e:
                logger.error(f"Неожиданная ошибка при опросе {client_name}: {e}")
                continue
        
        if not all_rates:
            logger.error("Не удалось получить данные ни от одного клиента")
            return False
        
        logger.info(f"Успешно получено {len(all_rates)} курсов от {successful_clients}/{len(self.api_clients)} клиентов")
        

        result_data = self._prepare_result_data(all_rates)
        
        try:
            self.storage.save(result_data)
            logger.info("Данные успешно сохранены в хранилище")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка при сохранении данных: {e}")
            return False

    def _prepare_result_data(self, rates: Dict[str, float]) -> Dict:
        """ Подготовка итогового объекта данных с метаданными.   """
        current_time = datetime.now(timezone.utc).isoformat()
        
        return {
            "meta": {
                "source": "ValutaTrade Hub Parser",
                "last_refresh": current_time,
                "rates_count": len(rates)
            },
            "rates": rates
        }