# example-empty-uv2

Учебный проект на Python 3.12+, содержащий collection of examples и демонстраций различных концепций и технологий.

## Структура проекта

```
example-empty-uv2/
├── main.py                     # Точка входа, запускает все примеры
├── config_log.py               # Настройка логирования
├── config_multi_proc_log.py    # Настройка логирования для мультипроцессорных приложений
├── pyproject.toml              # Зависимости и конфигурация проекта
├── uv.lock                     # Фиксированные версии зависимостей
├── start.bat                   # Скрипт запуска для Windows
├── reqs_all.txt                # Все зависимости
├── reqs_top.txt                # Основные зависимости
└── ex_*/                       # Примеры по различным темам
    ├── ex_work_process/        # Многопроцессорные приложения
    ├── ex_async_simple/        # Простой async/await
    ├── ex_async_with/          # Async context managers
    ├── ex_async_gen_iter/      # Async генераторы и итераторы
    ├── ex_metaclass/           # Метаклассы
    ├── ex_library/             # Работа с библиотеками (streamz и др.)
    ├── ex_file_zip/            # Работа с ZIP архивами
    ├── ex_code_war/            # Алгоритмические задачи и кодварс
    └── ex_all_others/          # Различные другие примеры
```

## Примеры

Каждая директория `ex_*` содержит самостоятельные примеры:

### ex_work_process
Демонстрации работы с multiprocessing, Process, Pool, Executor.

### ex_async_simple
Простые примеры async/await, gather, контекстных переменных.

### ex_async_with
Примеры использования async с context managers.

### ex_async_gen_iter
Async генераторы, асинхронные итераторы.

### ex_metaclass
Примеры создания и использования метаклассов.

### ex_library
Работа с внешними библиотеками: streamz, пользовательские потоки.

### ex_file_zip
Создание, чтение и модификация ZIP архивов без временных файлов.

### ex_code_war
Алгоритмические задачи: проверка скобок, разделение строк, операции с iadd.

### ex_all_others
Различные полезные примеры: trap task, диссемблирование, rich print, closure functions, deep copy, хеширование и др.

## Установка и запуск

```bash
# Установка зависимостей
uv sync

# Запуск всех примеров
python main.py

# Или через стартовый скрипт (Windows)
start.bat
```

## Требования

- Python 3.12+
- UV пакетный менеджер

## Зависимости

Основные зависимости указаны в pyproject.toml:
- ruff - линтер
- black - форматтер
- rich - богатый вывод в терминал
- sshtunnel - SSH туннелирования
- streamz - потоковая обработка данных
- aiosqlite - асинхронный SQLite

## Лицензия

MIT