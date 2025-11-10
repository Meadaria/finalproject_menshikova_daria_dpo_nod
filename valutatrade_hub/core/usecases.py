import json
from datetime import datetime
from pathlib import Path

from valutatrade_hub.core.constants import (
    MIN_PASSWORD_LENGTH,
    RATES_CACHE_TTL_HOURS,
)
from valutatrade_hub.core.currencies import get_currency
from valutatrade_hub.core.exceptions import (
    CurrencyNotFoundError,
    InsufficientFundsError,
)
from valutatrade_hub.core.models import Portfolio, User
from valutatrade_hub.core.session import get_current_user_id, set_current_user_id
from valutatrade_hub.decorators import log_action
from valutatrade_hub.infra.setting import settings
from valutatrade_hub.parser_service.config import parser_config
from valutatrade_hub.parser_service.storage import JsonFileStorage


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
    """Функция проверки, устарел ли кэш курсов"""
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
        return time_diff > RATES_CACHE_TTL_HOURS
    except Exception:
        return True

def _get_current_rates() -> dict:
    """Функция получения актуальных курсов из кэша парсера"""
    try:
        storage = JsonFileStorage(parser_config.RATES_FILE_PATH)
        data = storage.load()
        return data.get('rates', {}) if data else {}
    except Exception:
        return {}

def _get_exchange_rate(from_currency: str, to_currency: str,
                        rates: dict = None) -> float:
    """Функция получения курса между двумя валютами"""
    if not rates:
        rates = _get_current_rates()
    
    if from_currency == to_currency:
        return 1.0
    
    # Прямой курс
    pair_key = f"{from_currency}_{to_currency}"
    if pair_key in rates:
        return rates[pair_key]
    
    # Обратный курс
    reverse_pair_key = f"{to_currency}_{from_currency}"
    if reverse_pair_key in rates:
        return 1 / rates[reverse_pair_key]
    
    # Конвертация через USD
    from_to_usd = _get_exchange_rate(from_currency, "USD", rates)
    usd_to_to = _get_exchange_rate("USD", to_currency, rates)
    
    if from_to_usd and usd_to_to:
        return from_to_usd * usd_to_to
    
    return None

def _get_user_portfolio(user_id: int) -> tuple[Portfolio, int, list]:
    """Функция получения портфеля пользователя, его индекса и списка всех портфелей"""
    existing_portfolios_data = load_json_data("portfolios.json")
    existing_portfolios = [
        Portfolio.from_dict(portfolio_data) 
        for portfolio_data in existing_portfolios_data
    ]
    
    for i, portfolio in enumerate(existing_portfolios):
        if portfolio.user_id == user_id:
            return portfolio, i, existing_portfolios
    
    return None, -1, existing_portfolios

def _save_all_portfolios(portfolios: list) -> bool:
    """Функция сохранения всех портфелей"""
    all_portfolios_dicts = [portfolio.to_dict() for portfolio in portfolios]
    return save_json_data("portfolios.json", all_portfolios_dicts)

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
            crypto_pairs = [
                f"{crypto}_USD" for crypto in parser_config.CRYPTO_CURRENCIES
            ]
            crypto_rates = {k: v for k, v in rates.items() if k in crypto_pairs}
            rates = dict(sorted(
                crypto_rates.items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:top])

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

# =============================================================================
# CLI 
# =============================================================================


def register(username: str, password: str) -> bool:
    """Функция создания нового пользователя."""
    try:
        data_dir = settings.get("data_directory", "data/")

        Path(data_dir).mkdir(exist_ok=True)

        existing_users_data = load_json_data("users.json")  
        existing_users = [
            User.from_dict(user_data) for user_data in existing_users_data
        ]
        
        # Проверка существующего пользователя
        for user in existing_users:
            if user.username == username:
                print(f"Ошибка: пользователь '{username}' уже существует")
                return False
        
        if len(password) < MIN_PASSWORD_LENGTH:
            print(f"Пароль должен быть не короче"
                  f" {MIN_PASSWORD_LENGTH} символов")
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
        existing_portfolios = [
            Portfolio.from_dict(portfolio_data) 
            for portfolio_data in existing_portfolios_data
        ]
        
        new_portfolio = Portfolio(user_id=new_id, wallets={})
        
        all_portfolios_objects = existing_portfolios + [new_portfolio]
        all_portfolios_dicts = [
            portfolio.to_dict() for portfolio in all_portfolios_objects
        ]
        
        if not save_json_data("portfolios.json", all_portfolios_dicts):  
            print("Ошибка при сохранении портфелей")
            return False

        print(f"Пользователь '{username}' зарегистрирован (id={new_id}). "
              f"Войдите: login --username {username} --password ****")
        return True
        
    except Exception as e:
        print(f"Ошибка: {e}")
        return False
    
@log_action(action='LOGIN') 
def login(username: str, password: str):
    """Функция входа и фиксации текущей сессии"""
    try:
        existing_users_data = load_json_data("users.json")
        existing_users = [
            User.from_dict(user_data) for user_data in existing_users_data
        ]

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


def show_portfolio(base: str = 'USD') -> bool:
    """Функци показа портфеля с конвертацией по актуальным курсам из парсера"""
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

        user_portfolio, _, _ = _get_user_portfolio(current_user_id)
        if not user_portfolio:
            print("Портфель не найден")
            return False
                
        if not user_portfolio.wallets:
            print("Портфель пуст")
            return True

        current_rates = _get_current_rates()
        
        total_value = user_portfolio.get_total_value(base_code, current_rates)
        
        print(f"\n Портфель пользователя (ID: {current_user_id}) в {base_code}:")
        print("=" * 60)
        
        portfolio_summary = user_portfolio.get_portfolio_summary(current_rates)
        
        for currency_code, wallet_info in portfolio_summary["wallets"].items():
            balance = wallet_info["balance"]
            value_in_base = wallet_info.get("value_usd", 0)
            
            if wallet_info["rate_to_usd"] is not None:
                print(f"{currency_code}: {balance:.8f}"
                      f"≈ {value_in_base:.2f} {base_code}")
            else:
                print(f"{currency_code}: {balance:.8f} (курс неизвестен)")
        
        print("=" * 60)
        print(f"Общая стоимость: {total_value:.2f} {base_code}")

        if is_rates_cache_stale():
            print("\n Курсы могут быть устаревшими. Рекомендуется: update-rates")
        
        return True
        
    except Exception as e:
        print(f"Ошибка при показе портфеля: {e}")
        return False
  
@log_action(action='BUY')    
def buy(currency: str, amount: float) -> bool:
    """Функция покупки валюты с использованием актуальных курсов из парсера"""
    if not require_auth():
        return False
    
    try:
        if amount <= 0:
            print("Сумма покупки должна быть положительным числом")
            return False

        try:
            currency_obj = get_currency(currency)
            currency_code = currency_obj.code
        except CurrencyNotFoundError:
            print(f"Ошибка: валюта '{currency}' не найдена")
            return False
        
        current_user_id = get_current_user_id()

        user_portfolio, portfolio_index,all_portfolios = _get_user_portfolio(
            current_user_id
            )
        if not user_portfolio:
            print("Ошибка: портфель пользователя не найден")
            return False
        
        current_rates = _get_current_rates()
        
        exchange_rate = _get_exchange_rate(currency_code, "USD", current_rates)
        if not exchange_rate:
            try:
                exchange_rate = user_portfolio.get_exchange_rate(
                    currency_code, current_rates
                    )
            except ValueError as e:
                print(f"Ошибка: не удалось получить курс для {currency_code}: {e}")
                return False

        if not user_portfolio.has_currency(currency_code):
            user_portfolio.add_currency(currency_code, 0.0)

        wallet = user_portfolio.get_wallet(currency_code)
        old_balance = wallet.balance
        
        wallet.deposit(amount)
        new_balance = wallet.balance

        purchase_cost_usd = amount * exchange_rate
        
        if portfolio_index >= 0:
            all_portfolios[portfolio_index] = user_portfolio
        else:
            all_portfolios.append(user_portfolio)
            
        if not _save_all_portfolios(all_portfolios):
            print("Ошибка при сохранении портфеля")
            return False

        print(f"Покупка выполнена: {amount:.4f} {currency} по курсу "
              f"{exchange_rate:.2f} USD/{currency}")
        print("Изменения в портфеле:")
        print(f" - {currency}: было {old_balance:.4f} → стало {new_balance:.4f}")
        print(f"Оценочная стоимость покупки: {purchase_cost_usd:,.2f} USD")
        
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
            print("Сумма продажи должна быть положительным числом")
            return False
        
        try:
            currency_obj = get_currency(currency)
            currency_code = currency_obj.code
        except CurrencyNotFoundError:
            print(f"Ошибка: валюта '{currency}' не найдена")
            return False
        
        current_user_id = get_current_user_id()
        
        user_portfolio, portfolio_index, all_portfolios = _get_user_portfolio(
            current_user_id
            )
        if not user_portfolio:
            print("Ошибка: портфель пользователя не найден")
            return False
        
        # Проверка наличия валюты
        if not user_portfolio.has_currency(currency_code):
            print(f"Ошибка: валюта '{currency_code}' не найдена в портфеле")
            return False
        
        # Получение актуальных курсов из парсера
        current_rates = _get_current_rates()
        
        # Расчет курса через парсер
        exchange_rate = _get_exchange_rate(currency_code, "USD", current_rates)
        if not exchange_rate:
            try:
                exchange_rate = user_portfolio.get_exchange_rate(
                    currency_code, current_rates
                    )
            except ValueError as e:
                print(f"Ошибка: не удалось получить курс для {currency_code}: {e}")
                return False

        wallet = user_portfolio.get_wallet(currency_code)
        old_balance = wallet.balance

        if amount > old_balance:
            raise InsufficientFundsError(
                available=old_balance,
                required=amount, 
                code=currency_code
            )
        
        wallet.withdraw(amount)
        new_balance = wallet.balance
        
        # Расчет выручки и зачисление USD
        revenue_usd = amount * exchange_rate
        
        if revenue_usd > 0:
            if not user_portfolio.has_currency("USD"):
                user_portfolio.add_currency("USD", 0.0)
            usd_wallet = user_portfolio.get_wallet("USD")
            usd_wallet.deposit(revenue_usd)
        
        # Сохранение изменений
        if portfolio_index >= 0:
            all_portfolios[portfolio_index] = user_portfolio
        else:
            all_portfolios.append(user_portfolio)
            
        if not _save_all_portfolios(all_portfolios):
            print("Ошибка при сохранении портфеля")
            return False

        print(f"Продажа выполнена: {amount:.4f} {currency} по курсу "
              f"{exchange_rate:.2f} USD/{currency}")
        print("Изменения в портфеле:")
        print(f" - {currency}: было {old_balance:.4f} → стало {new_balance:.4f}")
        if revenue_usd > 0:
            print(f"Оценочная выручка: {revenue_usd:,.2f} USD")
        
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
        
        current_rates = _get_current_rates()
        rate = _get_exchange_rate(from_currency_code, to_currency_code, current_rates)
        
        if rate is not None:
            print(f" Курс: 1 {from_currency_code} ="
                  f" {rate:.6f} {to_currency_code}")
            
            storage = JsonFileStorage(parser_config.RATES_FILE_PATH)
            data = storage.load()
            last_refresh = data.get('meta', {}).get('last_refresh', 'неизвестно')
            print(f" Обновлено: {last_refresh}")
            
            if rate > 0:
                reverse_rate = 1 / rate
                print(f"Обратный курс: 1 {to_currency_code}"
                      f" = {reverse_rate:.6f} {from_currency_code}")
            
            # Предупреждение об устаревших курсах
            if is_rates_cache_stale():
                print("\nКурсы могут быть устаревшими. Рекомендуется: update-rates")
            
            return True
        else:
            print(f" Курс {from_currency_code} → {to_currency_code} не найден")
            print(" Попробуйте обновить курсы: update-rates")
            return False
            
    except CurrencyNotFoundError:
        print(" Ошибка: валюта не найдена")
        return False
    except Exception as e:
        print(f" Ошибка при получении курса: {e}")
        return False

def show_simple_help():
    """Показывает справку по командам"""
    print("\nДоступные команды:")
    print("  register (reg, r)  - регистрация нового пользователя")
    print("  login (log, l)     - вход в систему")
    print("  show-portfolio (port, p) - показать портфель")
    print("  buy (b)            - купить валюту")
    print("  sell (s)           - продать валюту")
    print("  rate               - получить курс валют")
    print("  update-rates       - обновить курсы валют")
    print("  show-rates         - показать кэшированные курсы")
    print("  logout (out)       - выход из системы")
    print("  help (?, h)        - эта справка")
    print("  exit (quit, q)     - выход из программы")