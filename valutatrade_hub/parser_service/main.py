#!/usr/bin/env python3

import argparse
import sys

from valutatrade_hub.parser_service.updater import RatesUpdater
from valutatrade_hub.parser_service.scheduler import Scheduler
from valutatrade_hub.parser_service.api_clients import CoinGeckoClient, ExchangeRateApiClient
from valutatrade_hub.parser_service.storage import JsonFileStorage
from valutatrade_hub.parser_service.config import parser_config


def main():
    parser = argparse.ArgumentParser(description='ValutaTrade Parser Service')
    parser.add_argument('command', choices=['update', 'schedule'], 
                       help='update - single update, schedule - run scheduler')
    parser.add_argument('--source', choices=['coingecko', 'exchangerate'],
                       help='Update from specific source only')
    
    args = parser.parse_args()
    
    clients = []
    
    clients.append(CoinGeckoClient(parser_config.CRYPTO_ID_MAP))
    
    if parser_config.EXCHANGERATE_API_KEY:
        clients.append(ExchangeRateApiClient(parser_config.EXCHANGERATE_API_KEY))
    
    storage = JsonFileStorage(parser_config.RATES_FILE_PATH)
    updater = RatesUpdater(clients, storage)
    
    if args.command == 'update':
        print("Parser Service: Starting update...")
        success = updater.run_update()
        sys.exit(0 if success else 1)
        
    elif args.command == 'schedule':
        print("Parser Service: Starting scheduler...")
        scheduler = Scheduler(updater, parser_config.UPDATE_INTERVAL)
        scheduler.start()
        
        try:
            while True:
                scheduler._stop_event.wait(1)
        except KeyboardInterrupt:
            print("\nParser Service: Shutting down...")
            scheduler.stop()


if __name__ == '__main__':
    main()