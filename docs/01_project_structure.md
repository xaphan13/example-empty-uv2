# Карта проекта: дерево, зависимости, инварианты окружения

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
├── .python-version             # Требуемая версия Python
├── README.md                   # Этот файл
├── AGENTS.md                   # Инструкции для агентов
├── QWEN.md                     # Контекст для главной сессии Qwen Code
├── .git/                       # Git репозиторий
├── .idea/                      # Настройки IDE
├── .venv/                      # Виртуальное окружение (не коммитится)
├── __pycache__/                # Кеш Python (не коммитится)
├── .ruff_cache/                # Кеш Ruff (не коммитится)
├── docs/                       # Документация на русском
│   ├── 01_project_structure.md
│   └── 02_examples_overview.md
└── ex_*/                       # Примеры по различным темам
    ├── ex_work_process/        # Многопроцессорные приложения
    │   ├── main_work_process.py
    │   ├── multi_process_demo.py
    │   ├── pool_executor_demo.py
    │   ├── multi_pool_demo.py
    │   ├── pool_executor_task.py
    │   ├── multi_process_class.py
    │   ├── multi_pool_worker.py
    │   └── __init__.py
    ├── ex_async_simple/        # Простой async/await
    │   ├── main_async_simple.py
    │   ├── one_task_not_error.py
    │   ├── gather_demo.py
    │   ├── demo_context_var.py
    │   └── __init__.py
    ├── ex_async_with/          # Async context managers
    │   ├── main_async_with.py
    │   ├── with_connection_factory.py
    │   ├── demo_create_session.py
    │   └── __init__.py
    ├── ex_async_gen_iter/      # Async генераторы и итераторы
    │   ├── main_async_gen_iter.py
    │   ├── demo_anext_asend.py
    │   ├── two_for_error_aclose.py
    │   └── __init__.py
    ├── ex_metaclass/           # Метаклассы
    │   ├── main_metaclass.py
    │   ├── noisy_meta.py
    │   ├── metaclass_mul_call.py
    │   ├── call_dunder_meta.py
    │   ├── vars_inside_func.py
    │   └── __init__.py
    ├── ex_library/             # Работа с библиотеками
    │   ├── main_library.py
    │   ├── stream_example.py
    │   ├── streamz_from_iterable.py
    │   ├── my_stream_map.py
    │   └── __init__.py
    ├── ex_file_zip/            # Работа с ZIP архивами
    │   ├── main_file.py
    │   ├── simple_zip.py
    │   ├── zip_no_temp.py
    │   ├── zip_read_extract.py
    │   └── __init__.py
    ├── ex_code_war/            # Алгоритмические задачи
    │   ├── main_code_war.py
    │   ├── valid_bracket.py
    │   ├── split_strings.py
    │   ├── iadd_demo.py
    │   └── __init__.py
    └── ex_all_others/          # Различные другие примеры
        ├── main_others.py
        ├── trap_task.py
        ├── ssh1.py
        ├── sobes11.py
        ├── rich_print.py
        ├── others_11.py
        ├── my_module.py
        ├── glob_mod.py
        ├── dis_module.py
        ├── dis_async_await.py
        ├── deep_copy_example.py
        ├── closure_func.py
        └── __init__.py
    └── ex_window_app_ttkbootstrap/  # GUI-пример на ttkbootstrap + pygubu
        ├── main_window_app.py   # Точка входа, парсит --smoke / --smoke-window
        ├── application_window.py # Класс ApplicationWindow, загрузка .ui, обработчики
        ├── example_runner.py    # Реестр примеров, запуск с захватом вывода
        ├── window_app.ui        # XML-разметка Pygubu
        └── __init__.py
```

## Зависимости

Основные зависимости указаны в pyproject.toml:
- ruff>=0.14.10 - линтер
- black>=25.0.0 - форматтер
- rich==14.2.0 - богатый вывод в терминал
- sshtunnel==0.4.0 - SSH туннелирования
- streamz==0.6.5 - потоковая обработка данных
- aiosqlite>=0.22.1 - асинхронный SQLite
- ttkbootstrap - тёмные темы оформления для Tk (используется в ex_window_app_ttkbootstrap)
- pygubu - загрузка XML-разметки интерфейса (используется в ex_window_app_ttkbootstrap)

Dev-зависимости (группа dev в pyproject.toml):
- pygubu-designer - визуальный дизайнер .ui-файлов для Pygubu

## Инварианты окружения

- Требуется Python 3.12+ (указано в .python-version)
- Используется UV как менеджер пакетов
- Виртуальное окружение создается в .venv/ через uv sync
- Логи пишутся в директорию, где запущен скрипт (обычно корень проекта)
- Для multiprocessing примеров может потребоваться защита точки входа `if __name__ == "__main__":`