# GUI-пример на ttkbootstrap + pygubu

Реализовать новый учебный пакет `ex_window_app_ttkbootstrap` с оконным
приложением: интерфейс загружается из `.ui`-файла Pygubu, стилизуется
ttkbootstrap, а из окна запускаются курируемые примеры проекта с захватом
их stdout/stderr и логов.

## Подтверждённые решения

- Запуск примеров — через импорт их агрегаторов (`main_*.py` пакетов `ex_*`),
  а не через `subprocess`.
- Результаты примера — захват `stdout`/`stderr` и записей логирования,
  вывод в текстовое поле окна.
- Курируемый набор примеров для GUI: 5 штук — `ex_async_simple`,
  `ex_code_war`, `ex_file_zip`, `ex_metaclass`, `ex_work_process`.
  Все они быстро завершаются и дают видимый вывод (print / logging).
- Зависимости: `ttkbootstrap` и `pygubu` — runtime; `pygubu-designer` — dev.
  Разрешение на добавление зависимостей получено.
- Полный smoke окна — под Xvfb: пользователь одобрил установку `xvfb` через
  `apt` (системное изменение); окно проверяется запуском под `xvfb-run`.
- Раскладка окна — на усмотрение разработчика; обязательные элементы:
  выбор примера, кнопка запуска, текстовое поле вывода, поле ввода/настройки,
  выпадающий список тем, индикатор процесса.
- Темы оформления — только тёмные: в выпадающем списке тем ttkbootstrap —
  `darkly`, `superhero`, `cyborg`, `solar`, `vapor`; тема по умолчанию —
  `darkly`.
- Имена пакета/модулей: `ex_window_app_ttkbootstrap`,
  `main_window_app.py`, `application_window.py`, `example_runner.py`,
  `window_app.ui`.
- Комментарии и docstrings — на русском.

## Результат

После задания в репозитории должны существовать:

- `pyproject.toml` / `uv.lock` с зависимостями `ttkbootstrap`, `pygubu`
  и dev-зависимостью `pygubu-designer`.
- Пакет `ex_window_app_ttkbootstrap/`:
  - `__init__.py`
  - `main_window_app.py` — точка входа, парсит `--smoke`.
  - `example_runner.py` — реестр примеров, запуск с захватом вывода.
  - `application_window.py` — класс окна, загрузка `.ui`, обработчики виджетов.
  - `window_app.ui` — XML-разметка Pygubu.
- Обновлённые `docs/01_project_structure.md` и `docs/02_examples_overview.md`
  с упоминанием нового примера.

Поведение:
- Обычный запуск открывает окно: пользователь выбирает пример, нажимает
  «Запустить», вывод появляется в текстовом поле.
- `python -m ex_window_app_ttkbootstrap.main_window_app --smoke [name]`
  запускает выбранный пример без создания окна, печатает захваченный вывод
  и завершается — headless-проверка для qa.

## Вне рамок

- Не добавлять GUI-пример в пакетный запуск `main.py` (окно заблокировало бы
  весь прогон).
- Не изменять существующие примеры `ex_*` ради GUI.
- Не писать юнит-тесты (в проекте их нет).
- Не добавлять зависимостей сверх `ttkbootstrap`, `pygubu`, `pygubu-designer`.
- Не поддерживать запуск примеров, требующих сети/SSH (исключаем
  `ex_library`, `ex_all_others.ssh1` и т.п.).

## План фаз

Единица исполнения — фаза: одно делегирование, 1–3 файла, бюджет ~10–15 ходов.
Следующая фаза стартует только после зелёного checkpoint и ревью диффа оркестратором.
Прогресс фазы разработчик фиксирует в `tasks/current/dev/phaseNN_progress.md`.

| # | Фаза | Исполнитель | Файлы | Контракт | Checkpoint | Бюджет ходов |
|---|---|---|---|---|---|---|
| 1 | Зависимости | backend-dev | `pyproject.toml`, `uv.lock` | runtime: `ttkbootstrap`, `pygubu`; dev: `pygubu-designer` | `uv sync` + import обеих runtime-библиотек | ~8 |
| 2 | Раннер примеров и UI-разметка | backend-dev | `ex_window_app_ttkbootstrap/__init__.py`, `ex_window_app_ttkbootstrap/example_runner.py`, `ex_window_app_ttkbootstrap/window_app.ui` | реестр из 5 примеров; API `list_examples()` / `run_example(name)`; stable id виджетов | ruff; headless-запуск раннера; парсинг `.ui` | ~12 |
| 3 | Оконный класс | backend-dev | `ex_window_app_ttkbootstrap/application_window.py` | `ApplicationWindow`; wiring виджетов; `threading` + `queue` + `after()` | ruff; `pygubu.Builder` загружает `.ui` без ошибок | ~14 |
| 4 | Точка входа и headless-smoke | backend-dev | `ex_window_app_ttkbootstrap/main_window_app.py` | `--smoke [name]` без импорта Tk; обычный запуск — mainloop | ruff; `python -m ... --smoke` выводит результат | ~10 |
| 5 | Документация | backend-dev | `docs/01_project_structure.md`, `docs/02_examples_overview.md` | новый пакет в дереве и в списке запуска | grep показывает упоминания нового примера | ~6 |

### Фаза 1: Зависимости

- Файлы: `pyproject.toml`, `uv.lock`.
- Контракт:
  - В `[project].dependencies` добавить `ttkbootstrap` и `pygubu`.
  - В `[dependency-groups] dev` добавить `pygubu-designer`.
  - `uv.lock` перегенерировать через `uv lock` или `uv sync`.
- Шаги:
  1. `uv add ttkbootstrap pygubu`.
  2. `uv add --dev pygubu-designer`.
  3. Убедиться, что `uv.lock` обновлён.
- Checkpoint:
  ```bash
  uv sync
  uv run python -c "import ttkbootstrap, pygubu; print(ttkbootstrap.__version__, pygubu.__version__)"
  ```
  Ожидание: обе библиотеки импортируются, версии напечатаны, exit 0.
- Готовность фазы: зависимости фиксированы в `uv.lock`, импорт работает.

### Фаза 2: Раннер примеров и UI-разметка

- Файлы:
  - `ex_window_app_ttkbootstrap/__init__.py`
  - `ex_window_app_ttkbootstrap/example_runner.py`
  - `ex_window_app_ttkbootstrap/window_app.ui`
- Контракт:
  - `example_runner.py` не импортирует `tkinter`/`ttkbootstrap`/`pygubu`;
    можно импортировать без дисплея.
  - Реестр примеров — `list[ExampleDescriptor]`:
    - `async_context_var` → `ex_async_simple.main_async_simple.run_simple_demo(None)`
    - `valid_bracket` → `ex_code_war.main_code_war.code_war_1(None)`
    - `zip_operations` → `ex_file_zip.main_file.run_file_zip(None)`
    - `metaclass_vars` → `ex_metaclass.main_metaclass.main_metaclass(None)`
    - `multiprocessing_demo` → `ex_work_process.main_work_process.run_process_demo()`
  - `run_example(name: str) -> str`:
    1. Временно перенаправляет `sys.stdout`/`sys.stderr` в `io.StringIO`.
    2. Временно добавляет `logging.QueueHandler` к корневому логгеру
       (уровень `INFO`) и собирает записи в очередь.
    3. Вызывает функцию примера.
    4. Восстанавливает потоки и логгер.
    5. Возвращает объединённую строку вывода.
  - `window_app.ui` — валидный XML Pygubu. Корневой виджет — `ttk.Frame`
    с id `main_frame`. Обязательные дочерние виджеты со stable id:
    - `example_combobox` — `ttk.Combobox` для выбора примера.
    - `theme_combobox` — `ttk.Combobox` для выбора тёмной темы ttkbootstrap
      (значения подставляет `application_window` из фазы 3: darkly,
      superhero, cyborg, solar, vapor; по умолчанию darkly).
    - `filter_entry` — `ttk.Entry` для фильтрации списка примеров.
    - `run_button` — `ttk.Button` для запуска.
    - `clear_button` — `ttk.Button` для очистки вывода.
    - `output_text` — `tk.Text` (или `ScrolledText`) для вывода.
    - `progressbar` — `ttk.Progressbar` (indeterminate mode).
    - `status_label` — `ttk.Label` для статуса.
- Шаги:
  1. Создать пакет и `__init__.py`.
  2. Реализовать `example_runner.py` с реестром и захватом вывода.
  3. Создать `window_app.ui` с перечисленными виджетами.
- Checkpoint:
  ```bash
  uv run ruff check ex_window_app_ttkbootstrap/
  uv run python -c "from ex_window_app_ttkbootstrap.example_runner import list_examples, run_example; print(list_examples()); print(run_example('valid_bracket'))"
  uv run python -c "import xml.etree.ElementTree as ET; ET.parse('ex_window_app_ttkbootstrap/window_app.ui')"
  ```
  Ожидание: ruff без ошибок; список из 5 имён и захваченный вывод напечатаны;
  XML распарсен без ошибок.
- Готовность фазы: раннер работает headless, `.ui` валиден как XML.

### Фаза 3: Оконный класс

- Файлы: `ex_window_app_ttkbootstrap/application_window.py`.
- Контракт:
  - Класс `ApplicationWindow`.
  - Создание окна и виджетов только внутри `__init__` / методов,
    не на уровне модуля.
  - Интеграция ttkbootstrap + pygubu:
    ```python
    self.window = ttkbootstrap.Window(title="...", themename="darkly")
    builder = pygubu.Builder()
    builder.add_from_file(ui_path)
    self.main_frame = builder.get_object("main_frame", self.window)
    self.main_frame.pack(fill="both", expand=True)
    ```
  - `ui_path` разрешается от файла модуля (`Path(__file__).with_name("window_app.ui")`),
    а не от cwd — грабля cwd-зависимости из AGENTS.md.
  - Привязка виджетов по id из фазы 2.
  - `theme_combobox` меняет тему через `ttkbootstrap.Style().theme_use(...)`;
    значения — только тёмные темы `darkly`, `superhero`, `cyborg`, `solar`,
    `vapor`; стартовая — `darkly`.
  - `filter_entry` фильтрует элементы `example_combobox` по вводу.
  - Запуск примера выполняется в `threading.Thread`.
  - Поток кладёт строки в `queue.Queue`; главный поток опрашивает очередь
    через `self.window.after(100, self._poll_queue)`.
  - `progressbar` запускается в indeterminate-режиме на время выполнения
    примера и останавливается по завершении.
  - `output_text` обновляется только из главного потока.
- Шаги:
  1. Создать `ApplicationWindow` с загрузкой `.ui` и привязкой виджетов.
  2. Реализовать фильтр, смену темы, запуск в потоке, доставку вывода.
  3. Добавить docstrings на русском.
- Checkpoint:
  ```bash
  uv run ruff check ex_window_app_ttkbootstrap/
  uv run python -c "from pygubu import Builder; b = Builder(); b.add_from_file('ex_window_app_ttkbootstrap/window_app.ui'); print('ui loaded')"
  uv run python -c "from ex_window_app_ttkbootstrap.application_window import ApplicationWindow; print('import ok')"
  ```
  Ожидание: ruff без ошибок; `.ui` загружен Builder'ом; импорт класса окна
  проходит без создания `Tk()` на уровне модуля. Если `Builder()` требует
  дисплей — допускается fallback на XML-парсинг из фазы 2, но импорт класса
  должен работать headless.
- Готовность фазы: окно собирается, виджеты связаны, интеграция pygubu
  валидна.

### Фаза 4: Точка входа и headless-smoke

- Файлы: `ex_window_app_ttkbootstrap/main_window_app.py`.
- Контракт:
  - `main()` парсит аргументы до импорта GUI.
  - `--smoke [name]`: импортирует только `example_runner`, запускает пример,
    печатает результат в stdout, exit 0. Если имя не указано — используется
    первый пример из реестра.
  - `--smoke-window [сек]`: создаёт `ApplicationWindow` и закрывает окно
    через N секунд (по умолчанию 5) через `window.after(...)`, exit 0 —
    полный smoke для прогона под `xvfb-run` без ручного закрытия.
  - Без флага `--smoke`: импортирует `ApplicationWindow`, создаёт окно,
    запускает `mainloop()`.
  - На уровне модуля не создаётся `Tk()` и не загружается `.ui`.
- Шаги:
  1. Реализовать парсинг `sys.argv`.
  2. В smoke-ветке вызвать `run_example` и напечатать результат.
  3. В GUI-ветке создать `ApplicationWindow` и запустить mainloop.
- Checkpoint:
  ```bash
  uv run ruff check ex_window_app_ttkbootstrap/
  uv run python -m ex_window_app_ttkbootstrap.main_window_app --smoke valid_bracket
  xvfb-run -a uv run python -m ex_window_app_ttkbootstrap.main_window_app --smoke-window 5
  ```
  Ожидание: ruff без ошибок; в выводе smoke-приложения присутствуют строки
  о проверке скобочных последовательностей (`isValid`), exit 0; smoke-window
  завершается сам через ~5 секунд с exit 0 (требует установленного xvfb —
  ставит оркестратор до прогона).
- Готовность фазы: headless-проверка запуска примера работает.

### Фаза 5: Документация

- Файлы: `docs/01_project_structure.md`, `docs/02_examples_overview.md`.
- Контракт:
  - В `01_project_structure.md` добавить `ex_window_app_ttkbootstrap/` в дерево
    со списком модулей.
  - В `02_examples_overview.md` добавить раздел с командой запуска
    `python -m ex_window_app_ttkbootstrap.main_window_app` и кратким
    описанием (GUI, ttkbootstrap, pygubu, запуск примеров).
- Шаги:
  1. Обновить дерево проекта.
  2. Добавить описание нового примера.
- Checkpoint:
  ```bash
  grep -q "ex_window_app_ttkbootstrap" docs/01_project_structure.md
  grep -q "main_window_app.py" docs/02_examples_overview.md
  ```
  Ожидание: обе команды grep возвращают 0.
- Готовность фазы: документация отражает новый пример.

## Критерии успеха

Проверяются qa по завершении всех фаз; сырые выводы — в `tasks/current/e2e/`.

| # | Критерий | Проверка | Ожидание |
|---|---|---|---|
| 1 | Runtime-зависимости установлены | `uv run python -c "import ttkbootstrap, pygubu"` | exit 0 |
| 2 | Ruff чист по новому пакету | `uv run ruff check ex_window_app_ttkbootstrap/` | нет ошибок |
| 3 | Раннер запускает пример headless и захватывает вывод | `uv run python -m ex_window_app_ttkbootstrap.main_window_app --smoke valid_bracket` | вывод содержит результат проверки скобок |
| 4 | `.ui`-файл валиден | `uv run python -c "from pygubu import Builder; b=Builder(); b.add_from_file('ex_window_app_ttkbootstrap/window_app.ui')"` | exit 0; если Builder требует дисплей — fallback на успешный XML-парсинг + работающий smoke |
| 5 | Импорт GUI-модуля не создаёт окно на уровне модуля | `uv run python -c "from ex_window_app_ttkbootstrap.application_window import ApplicationWindow; print('import ok')"` | exit 0, `Tk()` не создаётся при импорте |
| 6 | Документация обновлена | `grep` в `docs/` | присутствуют `ex_window_app_ttkbootstrap` и команда запуска |
| 7 | Окно собирается и закрывается под Xvfb | `xvfb-run -a uv run python -m ex_window_app_ttkbootstrap.main_window_app --smoke-window 5` | exit 0, traceback в выводе нет |

## Финальные критерии

1. Каждый критерий успеха подтверждён доказательством (e2e/, DEFECTS.md,
   ADVERSARIAL_REVIEW.md).
2. `tasks/current/DEFECTS.md` существует только если найдены дефекты; все записи
   не OPEN.
3. Adversarial-прогон выполнен, ни одна запись ADVERSARIAL_REVIEW.md не PENDING.

## Открытые вопросы

Открытых вопросов нет: проверка окна под Xvfb подтверждена пользователем
(см. «Подтверждённые решения»).
