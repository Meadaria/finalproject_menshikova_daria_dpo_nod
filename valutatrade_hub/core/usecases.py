import json 
from pathlib import Path
from datetime import datetime

from valutatrade_hub.core.models import User, Portfolio
from valutatrade_hub.core.session import get_current_user_id, set_current_user_id
from valutatrade_hub.core.exceptions import InsufficientFundsError, CurrencyNotFoundError, ApiRequestError
from valutatrade_hub.infra.setting import settings 
from valutatrade_hub.decorators import log_action 
from valutatrade_hub.core.currencies import get_currency
from valutatrade_hub.parser_service.storage import JsonFileStorage
from valutatrade_hub.parser_service.config import parser_config
from valutatrade_hub.parser_service.storage import JsonFileStorage
from valutatrade_hub.parser_service.config import parser_config
from valutatrade_hub.parser_service.storage import JsonFileStorage
from valutatrade_hub.parser_service.config import parser_config

def require_auth() -> bool:
    """Проверяет авторизацию пользователя"""
    if not get_current_user_id():
        print("Ошибка: необходимо войти в систему")
        return False
    return True

def load_json_data(filepath: str) -> list:
    """Функция загрузки данных из JSON файла, возвращает список"""
    data_dir = settings.get("data_directory", "data/")
    full_path = Path(data_dir) / filepath
    
    if full_path.exists():
        with open(full_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data if data else []
    return []

def save_json_data(filepath: str, data: list) -> bool:
    """Функция сохранения данных в JSON файл"""
    try:
        data_dir = settings.get("data_directory", "data/")
        full_path = Path(data_dir) / filepath
        
        Path(data_dir).mkdir(exist_ok=True)
        
        with open(full_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"Ошибка при сохранении данных в {filepath}: {e}")
        return False

def get_next_user_id(users_objects) -> int:
    """Функция присвоения следующего user_id из объектов User"""
    if not users_objects:
        return 1
    
    existing_ids = [user.user_id for user in users_objects]
    
    if existing_ids:
        return max(existing_ids) + 1
    else:
        return 1
    

def is_rates_cache_stale() -> bool:
    """Проверяет, устарел ли кэш курсов (старше 1 часа)"""
    try:
        storage = JsonFileStorage(parser_config.RATES_FILE_PATH)
        data = storage.load()
        
        if not data or not data.get('rates'):
            return True
            
        last_refresh = data.get('meta', {}).get('last_refresh')
        if not last_refresh:
            return True

        from datetime import datetime
        cache_time = datetime.fromisoformat(last_refresh.replace('Z', '+00:00'))
        current_time = datetime.now().astimezone()

        time_diff = (current_time - cache_time).total_seconds() / 3600
        return time_diff > 1  
        
    except Exception:
        return True


def register(username: str, password: str) -> bool:
    """Функция создания нового пользователя."""
    try:
        data_dir = settings.get("data_directory", "data/")
        filepath = str(Path(data_dir) / "users.json")
        portfolio_filepath = str(Path(data_dir) / "portfolios.json")

        Path(data_dir).mkdir(exist_ok=True)

        existing_users_data = load_json_data("users.json")  
        existing_users = [User.from_dict(user_data) for user_data in existing_users_data]
        
        # Проверка существующего пользователя
        for user in existing_users:
            if user.username == username:
                print(f"Ошибка: пользователь '{username}' уже существует")
                return False
        
        if len(password) < 4:
            print("Пароль должен быть не короче 4 символов")
            return False
        
        new_id = get_next_user_id(existing_users)
        new_user = User(
            user_id=new_id,
            username=username,
            hashed_password='temp',
            salt='temp',
            registration_date=datetime.now()
        )
        
        new_user.change_password(password)

        all_users_objects = existing_users + [new_user]
        all_users_dicts = [user.to_dict() for user in all_users_objects]
        
        if not save_json_data("users.json", all_users_dicts):  
            print("Ошибка при сохранении пользователей")
            return False

        existing_portfolios_data = load_json_data("portfolios.json")  
        existing_portfolios = [Portfolio.from_dict(portfolio_data) for portfolio_data in existing_portfolios_data]
        
        new_portfolio = Portfolio(user_id=new_id, wallets={})
        
        all_portfolios_objects = existing_portfolios + [new_portfolio]
        all_portfolios_dicts = [portfolio.to_dict() for portfolio in all_portfolios_objects]
        
        if not save_json_data("portfolios.json", all_portfolios_dicts):  
            print("Ошибка при сохранении портфелей")
            return False

        print(f"Пользователь '{username}' зарегистрирован (id={new_id}). Войдите: login --username {username} --password ****")
        return True
        
    except Exception as e:
        print(f"Ошибка: {e}")
        return False
    
@log_action(action='LOGIN') 
def login(username: str, password: str):
    """Функция входа и фиксации текущей сессии"""
    try:
        existing_users_data = load_json_data("users.json")
        existing_users = [User.from_dict(user_data) for user_data in existing_users_data]

        user_found = None
        for user in existing_users:
            if user.username == username:
                user_found = user
                break
            
        if not user_found:
            print(f"Пользователь '{username}' не найден")
            return False
        
        if user_found.verify_password(password):
            set_current_user_id(user_found.user_id)
            print(f"Успешный вход для пользователя '{username}'")
            

            if is_rates_cache_stale():
                print("Обновление курсов валют...")
                if update_rates():
                    print("Курсы успешно обновлены")
                else:
                    print("Предупреждение: не удалось обновить курсы")
            else:
                print("Курсы актуальны")
            
            return True
        else:
            print("Неверный пароль")
            return False
        
    except Exception as e:
        print(f"Ошибка: {e}")
        return False


def show_portfolio(base: str = 'USD'):
    """Функция показа портфолио"""
    if not require_auth():
        return False
    
    try:
        current_user_id = get_current_user_id()
        
        try:
            base_currency = get_currency(base)
            base_code = base_currency.code
        except CurrencyNotFoundError:
            print(f"Ошибка: базовая валюта '{base}' не найдена")
            return False
        
        existing_portfolios_data = load_json_data("portfolios.json")
        existing_portfolios = [Portfolio.from_dict(portfolio_data) for portfolio_data in existing_portfolios_data]
        
        user_portfolio = None
        for portfolio in existing_portfolios:
            if portfolio.user_id == current_user_id:
                user_portfolio = portfolio
                break
            
        if not user_portfolio:
            print("Портфель не найден")
            return False
                
        if not user_portfolio.wallets:
            print("Портфель пуст")
            return True

        
        storage = JsonFileStorage(parser_config.RATES_FILE_PATH)
        rates_data = storage.load()
        current_rates = rates_data.get('rates', {}) if rates_data else {}
        
        if base_code != "USD":
            base_to_usd_key = f"{base_code}_USD"
            if base_to_usd_key not in current_rates:

                usd_to_base_key = f"USD_{base_code}"
                if usd_to_base_key in current_rates:
                    base_to_usd_rate = 1 / current_rates[usd_to_base_key]
                else:
                    print(f"Ошибка: не удалось найти курс для базовой валюты '{base_code}'")
                    return False
            else:
                base_to_usd_rate = current_rates[base_to_usd_key]
        else:
            base_to_usd_rate = 1.0
        
        print(f"\nПортфель пользователя (ID: {current_user_id}) в {base_code}:")
        print("=" * 60)
        
        total_value = 0
        
        for currency_code, wallet in user_portfolio.wallets.items():
            balance = wallet.balance
            

            currency_to_usd_key = f"{currency_code}_USD"
            if currency_to_usd_key in current_rates:
                rate_to_usd = current_rates[currency_to_usd_key]

                value_in_base = (balance * rate_to_usd) / base_to_usd_rate
                total_value += value_in_base
                print(f"{currency_code}: {balance:.8f} ≈ {value_in_base:.2f} {base_code}")
            else:

                usd_to_currency_key = f"USD_{currency_code}"
                if usd_to_currency_key in current_rates:
                    rate_to_usd = 1 / current_rates[usd_to_currency_key]
                    value_in_base = (balance * rate_to_usd) / base_to_usd_rate
                    total_value += value_in_base
                    print(f"{currency_code}: {balance:.8f} ≈ {value_in_base:.2f} {base_code}")
                else:
                    print(f"{currency_code}: {balance:.8f} (курс неизвестен)")
        
        print("=" * 60)
        print(f"Общая стоимость: {total_value:.2f} {base_code}")
        
        return True
        
    except Exception as e:
        print(f"Ошибка при показе портфеля: {e}")
        return False
  
@log_action(action='BUY')    
def buy(currency: str, amount: float):
    """Функция покупки валюты"""
    if not require_auth():
        return False
    
    try:
        if amount <= 0:
            print("'amount' должен быть положительным числом")
            return False
        
        try:
            currency_obj = get_currency(currency)
            currency_code = currency_obj.code
        except CurrencyNotFoundError as e:
            print(f"Ошибка: валюта '{currency}' не найдена")
            return False
        

        current_user_id = get_current_user_id()

        existing_portfolios_data = load_json_data("portfolios.json")
        existing_portfolios = [Portfolio.from_dict(portfolio_data) for portfolio_data in existing_portfolios_data]
        
        user_portfolio = None
        portfolio_index = -1

        for i, portfolio in enumerate(existing_portfolios):
            if portfolio.user_id == current_user_id:
                user_portfolio = portfolio
                portfolio_index = i
                break
        
        if not user_portfolio:
            print("Ошибка: портфель пользователя не найден")
            return False
               
        if currency_code  not in user_portfolio.wallets:
            user_portfolio.add_currency(currency_code, 0.0)

        wallet = user_portfolio.get_wallet(currency_code)
        old_balance = wallet.balance

        wallet.deposit(amount)
        new_balance = wallet.balance

        exchange_rate = user_portfolio._exchange_rates.get(currency_code, 0)
        purchase_cost = amount * exchange_rate

        existing_portfolios[portfolio_index] = user_portfolio
        all_portfolios_dicts = [portfolio.to_dict() for portfolio in existing_portfolios]
        
        if not save_json_data("portfolios.json", all_portfolios_dicts):
            print("Ошибка при сохранении портфеля")
            return False

        print(f"Покупка выполнена: {amount:.4f} {currency} по курсу {exchange_rate:.2f} USD/{currency}")
        print("Изменения в портфеле:")
        print(f" - {currency}: было {old_balance:.4f} → стало {new_balance:.4f}")
        print(f"Оценочная стоимость покупки: {purchase_cost:,.2f} USD")
        
        return True
        
    except ValueError as e:
        print(f"Ошибка валидации: {e}")
        return False
    except Exception as e:
        print(f"Ошибка при покупке: {e}")
        return False

@log_action(action='SELL')
def sell(currency: str, amount: float):
    """Функция продажи валюты"""
    if not require_auth():
        return False
    
    try:
        if amount <= 0:
            print("'amount' должен быть положительным числом")
            return False
        
        try:
            currency_obj = get_currency(currency)
            currency_code = currency_obj.code
        except CurrencyNotFoundError as e:
            print(f"Ошибка: валюта '{currency}' не найдена")
            return False
        
        current_user_id = get_current_user_id()

        existing_portfolios_data = load_json_data("portfolios.json")
        existing_portfolios = [Portfolio.from_dict(portfolio_data) for portfolio_data in existing_portfolios_data]
        
        user_portfolio = None
        portfolio_index = -1

        for i, portfolio in enumerate(existing_portfolios):
            if portfolio.user_id == current_user_id:
                user_portfolio = portfolio
                portfolio_index = i
                break
            
        if not user_portfolio:
            print("Ошибка: портфель пользователя не найден")
            return False
               
        if currency_code not in user_portfolio.wallets:
            print(f"Ошибка: валюта '{currency_code}' не найдена в портфеле")
            return False
        
        wallet = user_portfolio.get_wallet(currency_code)
        old_balance = wallet.balance

        if amount > old_balance:
            raise InsufficientFundsError(
                available=old_balance,
                required=amount, 
                code=currency
            )

        wallet.withdraw(amount)
        new_balance = wallet.balance

        exchange_rate = user_portfolio._exchange_rates.get(currency, 0)
        revenue = amount * exchange_rate

        if revenue > 0:
            if "USD" not in user_portfolio.wallets:
                user_portfolio.add_currency("USD", 0.0)
            usd_wallet = user_portfolio.get_wallet("USD")
            usd_wallet.deposit(revenue)

        existing_portfolios[portfolio_index] = user_portfolio
        all_portfolios_dicts = [portfolio.to_dict() for portfolio in existing_portfolios]
        
        if not save_json_data("portfolios.json", all_portfolios_dicts):
            print("Ошибка при сохранении портфеля")
            return False

        print(f"Продажа выполнена: {amount:.4f} {currency} по курсу {exchange_rate:.2f} USD/{currency}")
        print("Изменения в портфеле:")
        print(f" - {currency}: было {old_balance:.4f} → стало {new_balance:.4f}")
        if revenue > 0:
            print(f"Оценочная выручка: {revenue:,.2f} USD")
        
        return True

    except InsufficientFundsError:
        raise
    except ValueError as e:
        print(f"Ошибка: {e}")
        return False
    except Exception as e:
        print(f"Ошибка при продаже: {e}")
        return False
        
def get_rate(from_currency: str, to_currency: str) -> bool:
    """Функция получения текущего курса из кэша парсера"""
    try:
        from_currency_obj = get_currency(from_currency)
        to_currency_obj = get_currency(to_currency)
        from_currency_code = from_currency_obj.code
        to_currency_code = to_currency_obj.code
           
        storage = JsonFileStorage(parser_config.RATES_FILE_PATH)
        data = storage.load()
        
        if not data or not data.get('rates'):
            print("Кэш курсов пуст. Используйте: update-rates")
            return False
        
        rates = data.get('rates', {})
        last_refresh = data.get('meta', {}).get('last_refresh', 'неизвестно')
        
        pair_key = f"{from_currency}_{to_currency}"
        reverse_pair_key = f"{to_currency}_{from_currency}"
        
        rate = None
        if pair_key in rates:
            rate = rates[pair_key]
        elif reverse_pair_key in rates:
            rate = 1 / rates[reverse_pair_key]
        
        if rate is not None:
            print(f"Курс: 1 {from_currency_code} = {rate:.6f} {to_currency_code}")
            print(f"Обновлено: {last_refresh}")
            
            if rate > 0:
                reverse_rate = 1 / rate
                print(f"Обратный курс: 1 {to_currency_code} = {reverse_rate:.6f} {from_currency_code}")
            return True
        else:
            print(f"Курс {from_currency_code} → {to_currency_code} не найден")
            return False
            
    except CurrencyNotFoundError as e:
        print(f"Ошибка: валюта не найдена")
        return False
    except Exception as e:
        print(f"Ошибка при получении курса: {e}")
        return False
    
# =============================================================================
# PARSER SERVICE INTEGRATION
# =============================================================================

def update_rates(source: str = None) -> bool:
    """Запустить обновление курсов через Parser Service"""
    import subprocess
    import sys
    
    try:
        cmd = [sys.executable, '-m', 'valutatrade_hub.parser_service.main', 'update']
        if source:
            cmd.extend(['--source', source])
            
        print("Запуск обновления курсов...")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("Курсы успешно обновлены")
            for line in result.stdout.split('\n'):
                if line.strip():
                    print(line)
            return True
        else:
            print("Ошибка при обновлении курсов")
            if result.stderr:
                print(result.stderr)
            return False
            
    except Exception as e:
        print(f"Ошибка запуска парсера: {e}")
        return False


def show_cached_rates(currency: str = None, top: int = None, base: str = "USD") -> bool:
    """Функция показа кэшированных курсов валют"""
    try:
       
        storage = JsonFileStorage(parser_config.RATES_FILE_PATH)
        data = storage.load()
        
        if not data or not data.get('rates'):
            print("Кэш курсов пуст. Используйте: update-rates")
            return False
        
        rates = data.get('rates', {})
        last_refresh = data.get('meta', {}).get('last_refresh', 'неизвестно')
        
        if currency:
            currency = currency.upper()
            rates = {k: v for k, v in rates.items() if currency in k}
            if not rates:
                print(f"Курс для '{currency}' не найден")
                return False
        
        if top:
            crypto_pairs = [f"{crypto}_USD" for crypto in ['BTC', 'ETH', 'SOL', 'ADA', 'DOT', 'DOGE']]
            crypto_rates = {k: v for k, v in rates.items() if k in crypto_pairs}
            rates = dict(sorted(crypto_rates.items(), key=lambda x: x[1], reverse=True)[:top])

        print(f"\nКурсы валют (обновлено: {last_refresh})")
        print("=" * 50)
        
        for pair, rate in sorted(rates.items()):
            if rate >= 1:
                print(f"{pair:<12} {rate:>12,.2f}")
            else:
                print(f"{pair:<12} {rate:>12.6f}")
        
        print("=" * 50)
        print(f"Всего курсов: {len(rates)}")
        return True
        
    except Exception as e:
        print(f"Ошибка отображения курсов: {e}")
        return False


def show_parser_help():
    """Показать справку по командам парсера"""
    print("\nКоманды управления курсами валют:")
    print("-" * 40)
    print("update-rates [source]    - обновить курсы валют")
    print("                          source: coingecko, exchangerate")
    print("show-rates               - показать все курсы")
    print("show-rates --currency X  - курс для валюты X")
    print("show-rates --top N       - топ-N криптовалют")
    print("show-rates --base X      - курсы в валюте X")

def show_simple_help():
    """Показывает справку по командам"""
    print("\nДоступные команды:")
    print("  register (reg, r)  - регистрация нового пользователя")
    print("  login (log, l)     - вход в систему")
    print("  portfolio (port, p) - показать портфель")
    print("  buy (b)            - купить валюту")
    print("  sell (s)           - продать валюту")
    print("  rate (r)           - получить курс валют")
    print("  update-rates       - обновить курсы валют")        
    print("  show-rates         - показать кэшированные курсы") 
    print("  logout (out)       - выход из системы")
    print("  clear (cls)        - очистить экран")
    print("  help (?, h)        - эта справка")
    print("  exit (quit, q)     - выход из программы")
    