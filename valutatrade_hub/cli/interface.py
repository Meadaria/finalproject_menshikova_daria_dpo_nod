import argparse
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from  valutatrade_hub.core.usecases  import register, login, show_portfolio, buy, sell, get_rate

def run():
    """Функция управления интерфейсом"""
    

    parser = argparse.ArgumentParser(
        description='Crypto Portfolio Manager',
        prog='portfolio-cli'
    )
    
    subparsers = parser.add_subparsers(
        dest='command',
        title='Команды',
        description='Доступные команды управления портфелем',
        help='Используйте <команда> --help для получения подробной информации'
    )
    
    # Команда register
    register_parser = subparsers.add_parser('register', help='Регистрация нового пользователя')
    register_parser.add_argument('--username', type=str, required=True, help='Имя пользователя')
    register_parser.add_argument('--password', type=str, required=True, help='Пароль (минимум 4 символа)')
    
    # Команда login
    login_parser = subparsers.add_parser('login', help='Вход в систему')
    login_parser.add_argument('--username', type=str, required=True, help='Имя пользователя')
    login_parser.add_argument('--password', type=str, required=True, help='Пароль')
    
    # Команда show-portfolio
    portfolio_parser = subparsers.add_parser('show-portfolio', help='Показать портфель')
    portfolio_parser.add_argument('--base', type=str, default='USD', 
                                 help='Базовая валюта для отображения (по умолчанию: USD)')
    
    # Команда buy
    buy_parser = subparsers.add_parser('buy', help='Купить валюту')
    buy_parser.add_argument('--currency', type=str, required=True, 
                           help='Код покупаемой валюты (например, BTC, ETH)')
    buy_parser.add_argument('--amount', type=float, required=True, 
                           help='Количество покупаемой валюты')
    
    # Команда sell
    sell_parser = subparsers.add_parser('sell', help='Продать валюту')
    sell_parser.add_argument('--currency', type=str, required=True, 
                            help='Код продаваемой валюты (например, BTC, ETH)')
    sell_parser.add_argument('--amount', type=float, required=True, 
                            help='Количество продаваемой валюты')
    
    # Команда get-rate
    rate_parser = subparsers.add_parser('get-rate', help='Получить курс валют')
    rate_parser.add_argument('--from', type=str, required=True, dest='from_currency',
                            help='Исходная валюта (например, USD)')
    rate_parser.add_argument('--to', type=str, required=True, dest='to_currency',
                            help='Целевая валюта (например, BTC)')
    
    # Парсинг аргументов
    args = parser.parse_args()
    
    match args.command:
        case 'register':
            register(args.username, args.password)
        
        case 'login':
            login(args.username, args.password)
        
        case 'show-portfolio':
            show_portfolio(args.base)
        
        case 'buy':
            buy(args.currency, args.amount)
        
        case 'sell':
            sell(args.currency, args.amount)
        
        case 'get-rate':
            get_rate(args.from_currency, args.to_currency)
        
        case _:
            parser.print_help()

