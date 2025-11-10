# Crypto Portfolio Manager

## Описание проекта
Веб-приложение для управления криптовалютным портфелем с автоматическим обновлением курсов валют через внешние API.

## Структура проекта
finalproject_menshikova_daria_dpo_nod/
├── README.md
├── pyproject.toml
├── poetry.lock
├── .env.example
├── .gitignore
├── logs/
│   ├── valutatrade.log
├── data/
│   ├── users.json
│   ├── portfolios.json
│   └── exchange_rates.json
├── valutatrade_hub/
│   ├── __init__.py
│   ├── cli/
│   │   ├── __init__.py
│   │   └── interface.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── models.py
│   │   ├── session.py
│   │   ├── usecases.py
│   │   ├── exceptions.py
│   │   ├── currencies.py
│   │   ├── constants.py
│   │   └── decorators.py
│   ├── parser_service/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── storage.py
│   │   ├── updater.py
│   │   └── scheduler.py
│   └── infra/
│       ├── __init__.py
│       └── setting.py

## Установка

### Требования
- Python 3.8+
- Poetry (менеджер зависимостей)

### Установка зависимостей
```bash
poetry install
```

## Запуск приложения

### Основное приложение
```bash
poetry run project
```

### Parser Service (отдельно)
```bash
poetry run python -m valutatrade_hub.parser_service.main update
```

## Примеры команд CLI

### Регистрация и авторизация
```bash
[guest]> register
Имя пользователя: alice
Пароль: 123456

[guest]> login
Имя пользователя: alice  
Пароль: 123456
```

### Управление портфелем
```bash
[user_1]> buy
Валюта: BTC
Количество: 0.5

[user_1]> sell
Валюта: ETH
Количество: 2

[user_1]> show-portfolio
Базовая валюта [USD]:
```

### Работа с курсами
```bash
[user_1]> rate
Из валюты: BTC
В валюту: USD

[user_1]> update-rates
```

## Кэш курсов и TTL

### Место хранения
Кэш курсов сохраняется в файл: `data/exchange_rates.json`

### Время жизни кэша (TTL)
- По умолчанию: 6 часов
- Настройка: через константу `RATES_CACHE_TTL_HOURS`

### Принудительное обновление
```bash
update-rates
```

## Настройка Parser Service

### Поддерживаемые источники
- **CoinGecko** - криптовалюты
- **ExchangeRate** - фиатные валюты

### Хранение API-ключей
Создайте файл `.env` в корне проекта:
```env
COINGECKO_API_KEY=your_coingecko_api_key
EXCHANGERATE_API_KEY=your_exchangerate_api_key
```

### Запуск с указанием источника
```bash
update-rates coingecko
update-rates exchangerate
```

### Автоматическое обновление
```bash
start-parser
```

## Дополнительные команды

### Просмотр кэшированных курсов
```bash
show-rates
show-rates --currency BTC
show-rates --top 10
show-rates --base EUR
```

### Справка
```bash
help
```

## Выход из приложения
```bash
exit
```
```
