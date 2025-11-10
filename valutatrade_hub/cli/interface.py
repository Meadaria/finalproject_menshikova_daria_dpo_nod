from valutatrade_hub.core.exceptions import (
    ApiRequestError,
    CurrencyNotFoundError,
    InsufficientFundsError,
)
from valutatrade_hub.core.session import get_current_user_id, logout
from valutatrade_hub.core.usecases import (
    buy,
    get_rate,
    login,
    register,
    sell,
    show_cached_rates,
    show_portfolio,
    show_simple_help,
    update_rates,
)


def run():
    """Основная функция CLI"""
    print("=== Crypto Portfolio Manager ===")
    print("Введите 'help' для списка команд")
    
    while True:
        try:
            
            user_id = get_current_user_id()
            status = f"user_{user_id}" if user_id else "guest"
            user_input = input(f"\n[{status}]> ").strip().lower()
            
            parts = user_input.split()
            cmd = parts[0] if parts else ""
            args = parts[1:] if len(parts) > 1 else []
            
            match cmd:
                case 'exit' | 'quit' | 'q':
                    print("Выход из программы.")
                    break
                    
                case 'register' | 'reg' | 'r':
                    username = input("Имя пользователя: ")
                    password = input("Пароль: ")
                    register(username, password)
                    
                case 'login' | 'log' | 'l':
                    username = input("Имя пользователя: ")
                    password = input("Пароль: ")
                    login(username, password)
                    
                case 'show-portfolio' | 'port' | 'p' | 'show':
                    base = input("Базовая валюта [USD]: ") or "USD"
                    show_portfolio(base)
                    
                case 'buy' | 'b':
                    try:
                        currency = input("Валюта: ").upper()
                        amount = float(input("Количество: "))
                        success = buy(currency, amount)
                        if success:
                            print(f"Покупка выполнена: {amount} {currency}")
                    except ValueError:
                        print("Ошибка: неверный формат количества")
                    except CurrencyNotFoundError:
                        print(f"Ошибка: валюта '{currency}' не поддерживается")
                    except InsufficientFundsError as e:
                        msg = (f"Ошибка: недостаточно средств. "
                               f"Доступно: {e.available:.4f} {e.code}")
                        print(msg)
                    except Exception as e:
                        print(f"Ошибка операции: {e}")
                    
                case 'sell' | 's':
                    try:
                        currency = input("Валюта: ").upper()
                        amount = float(input("Количество: "))
                        success = sell(currency, amount)
                        if success:
                            print(f"Продажа выполнена: {amount} {currency}")
                    except ValueError:
                        print("Ошибка: неверный формат количества")
                    except CurrencyNotFoundError:
                        print(f"Ошибка: валюта '{currency}' не поддерживается")
                    except InsufficientFundsError as e:
                        msg = (f"Ошибка: недостаточно средств. "
                               f"Доступно: {e.available:.4f} {e.code}")
                        print(msg)
                    except Exception as e:
                        print(f"Ошибка операции: {e}")
                    
                case 'rate' | 'курс':
                    try:
                        from_curr = input("Из валюты: ").upper()
                        to_curr = input("В валюту: ").upper()
                        
                        if not from_curr.strip() or not to_curr.strip():
                            print("Ошибка: необходимо указать обе валюты")
                            continue
                            
                        success = get_rate(from_curr, to_curr)
                        if not success:
                            print("Курс недоступен")
                    except CurrencyNotFoundError:
                        print("Ошибка: валюта не найдена")
                    except Exception as e:
                        print(f"Ошибка получения курса: {e}")
                
                case 'update-rates':
                    source = None
                    if args and args[0] in ['coingecko', 'exchangerate']:
                        source = args[0]
                    update_rates(source)
                        
                case 'show-rates':
                    currency = None
                    top = None
                    base = "USD"
                    
                    i = 0
                    while i < len(args):
                        if args[i] == '--currency' and i + 1 < len(args):
                            currency = args[i + 1]
                            i += 2
                        elif args[i] == '--top' and i + 1 < len(args):
                            try:
                                top = int(args[i + 1])
                                i += 2
                            except ValueError:
                                print("Ошибка: --top должен быть числом")
                                break
                        elif args[i] == '--base' and i + 1 < len(args):
                            base = args[i + 1]
                            i += 2
                        else:
                            i += 1
                    else:
                        show_cached_rates(currency=currency, top=top, base=base)
                    
                                   
                case 'logout' | 'out':
                    logout()
                    print("Выход выполнен")
                    
                case 'help' | '?' | 'h':
                    show_simple_help()
                                  
                case '':
                    continue
                    
                case _:
                    print(f"Неизвестная команда: '{cmd}'")
                    print("Введите 'help' для списка команд")
                
        except InsufficientFundsError:
            print("Ошибка: недостаточно средств")
        except CurrencyNotFoundError:
            print("Ошибка: валюта не найдена")
        except ApiRequestError:
            print("Ошибка: сервис недоступен")
        except KeyboardInterrupt:
            print("\nРабота программы завершена.")
            break
        except Exception as error:
            print(f"Ошибка: {error}")

if __name__ == "__main__":
    run()