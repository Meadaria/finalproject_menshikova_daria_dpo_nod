import json
from pathlib import Path
from models import User, Wallet, Portfolio
from datetime import datetime
from session import *

def load_json_data(filepath: str) -> list:
    """Функция загрузки данных из JSON файла, возвращает список"""
    if Path(filepath).exists():
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data if data else []
    return []

def get_next_user_id(users_objects) -> int:
    """Функция присвоения следущего user_id из объектов User"""
    if not users_objects:
        return 1
    max_id = max(user.user_id for user in users_objects)
    return max_id + 1

def register(username: str, password: str) -> bool:
    """Функция создания нового пользователя."""

    try:
        filepath = "data/users.json"
        portfolio_filepath = "data/portfolios.json" 

        Path("data/").mkdir(exist_ok=True)

        existing_users_data  = load_json_data(filepath)
        existing_users = [User.from_dict(user_data) for user_data in existing_users_data]
        
        for user in existing_users:
            if user.username == username:
                print(f"Ошибка: пользователь '{username}' уже существует")
                return False
        
        new_id = get_next_user_id(existing_users)
        new_user = User(
        user_id= new_id,
        username=username,
        hashed_password= 'temp',  
        salt='temp',
        registration_date=datetime.now()
    )
        
        new_user.change_password(password)

        all_users_objects = existing_users + [new_user]
        all_users_dicts = [user.to_dict() for user in all_users_objects]

        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(all_users_dicts, f, ensure_ascii=False, indent=2)

        existing_portfolios_data  = load_json_data(portfolio_filepath)
        existing_portfolios = [Portfolio.from_dict(portfolio_data) for portfolio_data in existing_portfolios_data]
        
        new_portfolio = Portfolio(user_id=new_id, wallets={})
        
        all_portfolios_objects = existing_portfolios + [new_portfolio]
        all_portfolios_dicts = [portfolio.to_dict() for portfolio in all_portfolios_objects]
        with open(portfolio_filepath, 'w', encoding='utf-8') as f:
            json.dump(all_portfolios_dicts, f, ensure_ascii=False, indent=2)


        print(f"Пользователь '{username}' зарегистрирован (id={new_id}). Войдите: login --username {username} --password ****")
        return True
        
    except Exception as e:
        print(f"Ошибка: {e}")
        return False
    
def login (username: str, password: str):
    """Функция входа и фиксации текущей сессии"""

    try:
        filepath = "data/users.json"

        if Path(filepath).exists():
            with open(filepath, 'r', encoding='utf-8') as f:
                users_data = json.load(f)
                if users_data:
                    existing_users = [User.from_dict(user_data) for user_data in users_data]

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
            return True
        else:
            print("Неверный пароль")
            return False
        
    except Exception as e:
        print(f"Ошибка: {e}")
        return False

def show_portfolio(base:str = 'USD'):
    """Функция показа портфолио"""

    try:
        current_user_id = get_current_user_id()
        if not current_user_id:
            print("Ошибка: необходимо войти в систему")
            return False
        
        portfolio_filepath = "data/portfolios.json"
        existing_portfolios_data = load_json_data(portfolio_filepath)
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
        
        print(f"\nПортфель пользователя (ID: {current_user_id}):")
        print("=" * 50)

        total_value = user_portfolio.get_total_value(base)
        
        for currency_code, wallet in user_portfolio.wallets.items():
            balance = wallet.balance
            if currency_code in user_portfolio._exchange_rates:
                rate = user_portfolio._exchange_rates[currency_code]
                value_in_base = balance * rate
                print(f"{currency_code}: {balance:.8f} ≈ {value_in_base:.2f} {base}")
            else:
                print(f"{currency_code}: {balance:.8f} (курс неизвестен)")
        
        print("=" * 50)
        print(f"Общая стоимость: {total_value:.2f} {base}")
        
        return True
        
    except Exception as e:
        print(f"Ошибка при показе портфеля: {e}")
        return False
    
def buy(currency: str, amount: float):
    """Функция покупки валюты"""

    try:
        current_user_id = get_current_user_id()
        if not current_user_id:
            print("Ошибка: необходимо войти в систему")
            return False
        
        portfolio_filepath = "data/portfolios.json"
        existing_portfolios_data = load_json_data(portfolio_filepath)
        existing_portfolios = [Portfolio.from_dict(portfolio_data) for portfolio_data in existing_portfolios_data]
        
        user_portfolio = None
        portfolio_index = -1

        for i, portfolio in enumerate(existing_portfolios):
            if portfolio.user_id == current_user_id:
                user_portfolio = portfolio
                portfolio_index = i
                break
               
        if currency not in user_portfolio.wallets:
            user_portfolio.add_currency(currency, 0.0)

        wallet = user_portfolio.get_wallet(currency)
        old_balance = wallet.balance

        wallet.deposit(amount)
        new_balance = wallet.balance

        exchange_rate = user_portfolio._exchange_rates.get(currency, 0)
        purchase_cost = amount * exchange_rate

        existing_portfolios[portfolio_index] = user_portfolio

        all_portfolios_dicts = [portfolio.to_dict() for portfolio in existing_portfolios]
        with open(portfolio_filepath, 'w', encoding='utf-8') as f:
            json.dump(all_portfolios_dicts, f, ensure_ascii=False, indent=2)

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

def sell(currency: str, amount: float):
    """Функция продажи валюты"""

    try:
        current_user_id = get_current_user_id()
        if not current_user_id:
            print("Ошибка: необходимо войти в систему")
            return False
        
        portfolio_filepath = "data/portfolios.json"
        existing_portfolios_data = load_json_data(portfolio_filepath)
        existing_portfolios = [Portfolio.from_dict(portfolio_data) for portfolio_data in existing_portfolios_data]
        
        user_portfolio = None
        portfolio_index = -1

        for i, portfolio in enumerate(existing_portfolios):
            if portfolio.user_id == current_user_id:
                user_portfolio = portfolio
                portfolio_index = i
                break
               
        if currency not in user_portfolio.wallets:
            print(f"Ошибка: валюта '{currency}' не найдена в портфеле")
            return False
        
        wallet = user_portfolio.get_wallet(currency)
        old_balance = wallet.balance

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
        with open(portfolio_filepath, 'w', encoding='utf-8') as f:
            json.dump(all_portfolios_dicts, f, ensure_ascii=False, indent=2)

        print(f"Продажа выполнена: {amount:.4f} {currency} по курсу {exchange_rate:.2f} USD/{currency}")
        print("Изменения в портфеле:")
        print(f" - {currency}: было {old_balance:.4f} → стало {new_balance:.4f}")
        if revenue > 0:
            print(f"Оценочная выручка: {revenue:,.2f} USD")
        
        return True

    except ValueError as e:
        print(f"Ошибка: {e}")
        return False
    except Exception as e:
        print(f"Ошибка при продаже: {e}")
        return False
        
def get_rate(from_currency: str, to_currency: str) -> bool:
    """Функция получения текущего курса одной валюты к другой"""
    
    try:
        
        try:
            temp_from = Wallet(from_currency, 0.0)
            temp_to = Wallet(to_currency, 0.0)
            from_currency = temp_from.currency_code
            to_currency = temp_to.currency_code
        except ValueError as e:
            print(f"Ошибка валидации валюты: {e}")
            return False
        
        
        rates_filepath = "data/rates.json"
        rates_data = load_json_data(rates_filepath) or {}
        
        current_time = datetime.now()
        cache_valid = False
        rate = None
        updated_at = None
        
     
        if rates_data and "last_refresh" in rates_data:
            cache_time = datetime.fromisoformat(rates_data["last_refresh"])
            if current_time - cache_time < timedelta(minutes=5):
                cache_valid = True
        
       
        pair_key = f"{from_currency}_{to_currency}"
        reverse_pair_key = f"{to_currency}_{from_currency}"
        
        
        if cache_valid:
            if pair_key in rates_data:
                rate_info = rates_data[pair_key]
                rate = rate_info.get("rate")
                updated_at = rate_info.get("updated_at")
            elif reverse_pair_key in rates_data:
                rate_info = rates_data[reverse_pair_key]
                reverse_rate = rate_info.get("rate")
                if reverse_rate:
                    rate = 1 / reverse_rate
                    updated_at = rate_info.get("updated_at")
        

        if not cache_valid or rate is None:
            print("Обновление курсов...")
            rates_data = _get_stub_rates_data()  
            
            with open(rates_filepath, 'w', encoding='utf-8') as f:
                json.dump(rates_data, f, ensure_ascii=False, indent=2)
            
            if pair_key in rates_data:
                rate_info = rates_data[pair_key]
                rate = rate_info.get("rate")
                updated_at = rate_info.get("updated_at")
            elif reverse_pair_key in rates_data:
                rate_info = rates_data[reverse_pair_key]
                reverse_rate = rate_info.get("rate")
                if reverse_rate:
                    rate = 1 / reverse_rate
                    updated_at = rate_info.get("updated_at")
        
        if rate is not None:
            print(f"Курс: 1 {from_currency} = {rate:.6f} {to_currency}")
            if updated_at:
                updated_time = datetime.fromisoformat(updated_at)
                print(f"Обновлено: {updated_time.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"Источник: {rates_data.get('source', 'ParserService')}")
            return True
        else:
            print(f"Ошибка: не удалось получить курс {from_currency} → {to_currency}")
            return False
            
    except Exception as e:
        print(f"Ошибка при получении курса: {e}")
        return False

def _get_stub_rates_data() -> dict:
    """Заглушка обменных курсов в правильном формате"""
    current_time = datetime.now().isoformat()
    
    return {
        "EUR_USD": {
            "rate": 1.0786,
            "updated_at": current_time
        },
        "BTC_USD": {
            "rate": 59337.21,
            "updated_at": current_time
        },
        "ETH_USD": {
            "rate": 3720.00,
            "updated_at": current_time
        },
        "RUB_USD": {
            "rate": 0.01016,
            "updated_at": current_time
        },
        "USD_EUR": {
            "rate": 0.9271,  # 1 / 1.0786
            "updated_at": current_time
        },
        "USD_BTC": {
            "rate": 0.00001685,  # 1 / 59337.21
            "updated_at": current_time
        },
        "source": "ParserService",
        "last_refresh": current_time
    }





    

    




