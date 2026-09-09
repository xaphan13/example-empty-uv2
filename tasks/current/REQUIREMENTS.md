# Текущее задание — Перевод GUI-примера с ttkbootstrap на CustomTkinter

Пересобрать существующий GUI-пример `ex_window_app_ttkbootstrap` на библиотеке CustomTkinter: сохранить логику запуска примеров и API `example_runner.py`, но полностью заменить визуальную оболочку — современный тёмный интерфейс со скруглёнными кнопками, карточками, акцентными цветами и hover-эффектами. Пакет переименовать в `ex_window_app_customtkinter`, `ttkbootstrap` удалить из зависимостей, `customtkinter` добавить.

## Подтверждённые решения

- UI-библиотека — **CustomTkinter** (`customtkinter`) вместо `ttkbootstrap`; `ttkbootstrap` удалить из `pyproject.toml`/`uv.lock`.
- **pygubu сохраняется**: разметка остаётся в `window_app.ui`, но на CTk-виджетах через плагин `pygubu.plugins.customtkinter`.
- Раскладка — **сайдбар слева + контент справа**: в сайдбаре поле поиска и карточки 5 примеров с краткими описаниями; в контенте — панель вывода («терминал», моноширинный шрифт), крупная акцентная кнопка «Запустить», прогресс-индикатор, статусная строка.
- Выбор примера — **только кликом по карточке** в сайдбаре; комбобокс выбора не возвращается, поиск фильтрует карточки (решение пользователя).
- Тема — **статичная тёмная**: `set_appearance_mode("Dark")` + `set_default_color_theme("blue")` в коде, без переключателя тем — в CustomTkinter смена темы на лету применяется только к новым виджетам (решение пользователя).
- Цветовая палитра — **зафиксирована точно** как в разделе «Цветовая палитра», без свободы подбора для разработчика (решение пользователя).
- Логика запуска примеров **не трогается**: `example_runner.py` сохраняет реестр из 5 примеров и API `list_examples()` / `run_example()`.
- Пакет **переименовать** в `ex_window_app_customtkinter` через `git mv`, правку импортов, docstring'ов и документации.
- `main_window_app.py` не меняет семантики: `--smoke [name]` (headless, exit 0/2) и `--smoke-window [sec]` (окно + автозакрытие через `after`) сохраняются с теми же аргументами.
- Дизайн-требования жёстко зафиксированы в спеке: тёмная тема, скругления, акцент, отступы, hover — см. раздел «Дизайн-спецификация».
- `main.py` не трогать; другие `ex_*` не трогать; тесты не писать; новых зависимостей кроме `customtkinter` не добавлять.

## Результат

После задания в репозитории должны существовать:

- `pyproject.toml` / `uv.lock` с `customtkinter` в runtime-зависимостях, без `ttkbootstrap`; `pygubu` и `pygubu-designer` остаются.
- Пакет `ex_window_app_customtkinter/` (переименованный из `ex_window_app_ttkbootstrap`):
  - `__init__.py` — маркер пакета с новым именем.
  - `main_window_app.py` — точка входа, парсит `--smoke [name]` / `--smoke-window [sec]`, лениво импортирует GUI.
  - `example_runner.py` — без изменений логики (реестр, захват вывода).
  - `application_window.py` — класс `ApplicationWindow` на CustomTkinter + pygubu Builder.
  - `window_app.ui` — XML-разметка Pygubu на CTk-виджетах (см. дизайн-спецификацию).
- Обновлённые `docs/01_project_structure.md` и `docs/02_examples_overview.md` с новым именем пакета.

Поведение:
- Обычный запуск открывает окно: пользователь выбирает пример (кликом по карточке в сайдбаре), нажимает «Запустить», вывод появляется в текстовом поле.
- `python -m ex_window_app_customtkinter.main_window_app --smoke [name]` запускает пример без окна.
- `python -m ex_window_app_customtkinter.main_window_app --smoke-window [сек]` поднимает окно и закрывает автоматически.

## Вне рамок

- Не изменять `example_runner.py` (реестр, захват stdout/stderr/логов).
- Не добавлять GUI-пример в `main.py`.
- Не изменять существующие примеры `ex_*`.
- Не писать юнит-тесты.
- Не добавлять зависимостей сверх `customtkinter`.
- Не поддерживать запуск примеров вне реестра.

## Дизайн-спецификация

### Общая раскладка

- Корневое окно создаётся программно в `application_window.py`: `ctk.CTk()` после `ctk.set_appearance_mode("Dark")` и `ctk.set_default_color_theme("blue")`. Корневой объект `.ui` — `CTkFrame` id `main_frame`, он встраивается в окно (не полагаемся на непроверенные атрибуты CTk-корня в плагине pygubu).
- `main_frame` — `CTkFrame` с `fg_color` тёмного фона `#121212`, `corner_radius=0`, растянут на всё окно.
- `main_frame` разбит на два столбца grid:
  - **Сайдбар** (`CTkFrame` id `sidebar_frame`, ширина фиксированная ~260 px): `fg_color="#1e1e1e"`, `corner_radius=12`.
  - **Контент** (`CTkFrame` id `content_frame`, expand): `fg_color="#151515"`, `corner_radius=12`.
- Отступы (padx/pady) — 12–16 px между сайдбаром и контентом, 8 px внутри секций.

### Сайдбар

- Заголовок `CTkLabel` id `sidebar_title`: текст «Примеры», шрифт `{Arial} 16 {bold}`, `text_color="#e0e0e0"`.
- Поле поиска `CTkEntry` id `search_entry`: `placeholder_text="Поиск примера..."`, `corner_radius=8`, `fg_color="#2b2b2b"`, `border_color="#3a3a3a"`, `text_color="#e0e0e0"`, `placeholder_text_color="#6e6e6e"`.
- Список карточек — `CTkScrollableFrame` id `cards_scroll` (чтобы 5 карточек не ломались при уменьшении окна): `fg_color="transparent"`, `corner_radius=0`.
- Каждая карточка — `CTkFrame` id `card_{example_id}` (5 штук), `corner_radius=10`, `fg_color="#252525"`, `border_width=1`, `border_color="#333333"`:
  - `CTkLabel` id `card_title_{example_id}` — заголовок примера, шрифт `{Arial} 12 {bold}`, `text_color="#f0f0f0"`.
  - `CTkLabel` id `card_desc_{example_id}` — однострочное описание, шрифт `{Arial} 10 {}`, `text_color="#a0a0a0"`, `wraplength=220`.
  - Карточка кликабельна: через `bind("<Button-1>", ...)` в `application_window.py` выбирает пример (эквивалент старого `example_combobox`).
  - Hover-эффект карточки: при наведении `fg_color` меняется на `#2f2f2f` через `bind("<Enter>")` / `bind("<Leave>")`.
  - Выбранная карточка подсвечивается: `border_color="#3b8ed0"`, `fg_color="#2a3a4a"`.

### Контент

- Панель вывода `CTkTextbox` id `output_text`: `font="{JetBrains Mono} 10 {}"` (или `{Consolas} 10 {}`), `fg_color="#0d0d0d"`, `text_color="#d4d4d4"`, `border_color="#2a2a2a"`, `corner_radius=8`, `wrap="word"`, `state="normal"` для записи.
- Кнопка «Запустить» `CTkButton` id `run_button`: `text="Запустить"`, `corner_radius=10`, `fg_color="#3b8ed0"`, `hover_color="#2c6fa3"`, `text_color="#ffffff"`, `font="{Arial} 12 {bold}"`, `width=140`, `height=36`.
- Кнопка «Очистить» `CTkButton` id `clear_button`: `text="Очистить"`, `corner_radius=10`, `fg_color="#3a3a3a"`, `hover_color="#4a4a4a"`, `text_color="#e0e0e0"`, `width=100`, `height=32`.
- Прогресс-индикатор `CTkProgressBar` id `progressbar`: `fg_color="#2a2a2a"`, `progress_color="#3b8ed0"`, `corner_radius=6`. Анимация «выполняется» — через `.start()` / `.stop()`; у `CTkProgressBar` нет ttk-опции `mode`, точный набор опций (например, `indeterminate_speed`) сверить с установленной версией customtkinter на фазе 3.
- Статусная строка `CTkLabel` id `status_label`: `text="Готово"`, `text_color="#909090"`, `font="{Arial} 10 {}"`.

### Цветовая палитра

- Фон окна: `#121212`.
- Фон сайдбара: `#1e1e1e`.
- Фон контента: `#151515`.
- Карточка: `#252525`, бордюр `#333333`.
- Акцент: `#3b8ed0` (кнопка запуска, прогресс, выделенная карточка).
- Акцент hover: `#2c6fa3`.
- Текст основной: `#e0e0e0`.
- Текст вторичный: `#a0a0a0`.
- Терминал (вывод): `#0d0d0d` / `#d4d4d4`.
- Скругления: карточки/рамки `10`, кнопки/поля/текстбокс `8`, прогрессбар `6`.

### Тема CustomTkinter

- В `application_window.py` при создании окна вызвать:
  - `ctk.set_appearance_mode("Dark")`
  - `ctk.set_default_color_theme("blue")`
- Переключатель тем ttkbootstrap удаляется (`theme_combobox` и `_DARK_THEMES` уходят). Цвета виджетов задаются явно через `fg_color`/`hover_color`/`border_color` в `.ui` и коде.

## План фаз

Единица исполнения — фаза: одно делегирование, 1–3 файла, бюджет ~10–15 ходов. Следующая фаза стартует только после зелёного checkpoint и ревью диффа оркестратором. Прогресс фазы разработчик фиксирует в `tasks/current/dev/phaseNN_progress.md`.

| # | Фаза | Исполнитель | Файлы | Контракт | Checkpoint | Бюджет ходов |
|---|---|---|---|---|---|---|
| 1 | Зависимости | backend-dev | `pyproject.toml`, `uv.lock` | runtime: заменить `ttkbootstrap` на `customtkinter`; `pygubu` остаётся; dev: `pygubu-designer` остаётся | `uv sync` + import `customtkinter` и `pygubu` | ~8 |
| 2 | Переименование пакета | backend-dev | `ex_window_app_ttkbootstrap/` → `ex_window_app_customtkinter/` (git mv) | все 5 файлов под новым именем; импорты и docstring'ы обновлены | ruff + headless import всех модулей | ~10 |
| 3 | UI-разметка на CTk | backend-dev | `ex_window_app_customtkinter/window_app.ui` | корневой `CTk`/`CTkFrame`, stable id: `main_frame`, `sidebar_frame`, `content_frame`, `search_entry`, `cards_scroll`, `card_*`, `output_text`, `run_button`, `clear_button`, `progressbar`, `status_label` | Builder загружает `.ui` без ошибок под Xvfb | ~14 |
| 4 | Оконный класс | backend-dev | `ex_window_app_customtkinter/application_window.py` | `ApplicationWindow` на CustomTkinter; wiring виджетов; клик по карточке выбирает пример; запуск в `threading.Thread` + `queue` + `after()` | ruff; smoke-window под Xvfb | ~15 |
| 5 | Точка входа | backend-dev | `ex_window_app_customtkinter/main_window_app.py` | переименование импортов/текстов; `--smoke` и `--smoke-window` с прежней семантикой | ruff; `--smoke valid_bracket`; `--smoke-window 5` | ~10 |
| 6 | Документация | backend-dev | `docs/01_project_structure.md`, `docs/02_examples_overview.md` | новое имя пакета, команда запуска, описание CustomTkinter | grep нового имени и команды | ~6 |

### Фаза 1: Зависимости

- Файлы: `pyproject.toml`, `uv.lock`.
- Контракт:
  - В `[project].dependencies` удалить `ttkbootstrap>=2.2.2`.
  - В `[project].dependencies` добавить `customtkinter>=5.2.0`.
  - `pygubu>=0.42.1` остаётся; dev-группа `pygubu-designer>=0.46.1` остаётся.
  - `uv.lock` перегенерировать через `uv lock` / `uv sync`.
- Шаги:
  1. `uv remove ttkbootstrap`.
  2. `uv add customtkinter`.
  3. Убедиться, что `uv.lock` обновлён.
- Checkpoint:
  ```bash
  uv sync
  uv run python -c "import customtkinter as ctk, pygubu; print(ctk.__version__, pygubu.__version__)"
  ```
  Ожидание: обе библиотеки импортируются, версии напечатаны, exit 0.
- Готовность фазы: зависимости фиксированы, `ttkbootstrap` отсутствует в `pyproject.toml`/`uv.lock`.

### Фаза 2: Переименование пакета

- Файлы: весь каталог `ex_window_app_ttkbootstrap/` (5 файлов).
- Контракт:
  - `git mv ex_window_app_ttkbootstrap ex_window_app_customtkinter`.
  - Во всех `.py` заменить `ex_window_app_ttkbootstrap` на `ex_window_app_customtkinter` (импорты, docstring'и, тексты помощи argparse).
  - Логика `example_runner.py`, `application_window.py`, `main_window_app.py` не меняется — только переименование.
- Шаги:
  1. `git mv` каталога.
  2. Массовая замена имени пакета во всех файлах каталога.
  3. Обновить docstring'и `__init__.py` и module-level комментарии.
- Checkpoint:
  ```bash
  uv run ruff check ex_window_app_customtkinter/
  uv run python -c "from ex_window_app_customtkinter.example_runner import list_examples, run_example; print([e.example_id for e in list_examples()])"
  uv run python -c "from ex_window_app_customtkinter.application_window import ApplicationWindow; print('import ok')"
  uv run python -c "import ex_window_app_customtkinter.main_window_app; print('import ok')"
  grep -R "ex_window_app_ttkbootstrap" ex_window_app_customtkinter/ && exit 1 || exit 0
  ```
  Ожидание: ruff без ошибок; импорты работают headless; старое имя не встречается внутри пакета.
- Готовность фазы: пакет переименован, импорты и тексты синхронизированы.

### Фаза 3: UI-разметка на CTk

- Файлы: `ex_window_app_customtkinter/window_app.ui`.
- Контракт:
  - Корневой объект — `customtkinter.CTkFrame` id `main_frame` (`corner_radius=0`, `fg_color="#121212"`), растянут на всё окно (`fill="both"`, `expand="true"`). Окно `ctk.CTk()` и тему (`set_appearance_mode("Dark")` + `set_default_color_theme("blue")`) создаёт код в `application_window.py` (фаза 4).
  - `main_frame` содержит `customtkinter.CTkFrame` id `sidebar_frame` (столбец 0) и `customtkinter.CTkFrame` id `content_frame` (столбец 1, expand).
  - В `sidebar_frame`:
    - `CTkLabel` id `sidebar_title`.
    - `CTkEntry` id `search_entry`.
    - `CTkScrollableFrame` id `cards_scroll`.
    - Внутри `cards_scroll` — 5 карточек `CTkFrame` id `card_{example_id}` (id: `card_async_context_var`, `card_valid_bracket`, `card_zip_operations`, `card_metaclass_vars`, `card_multiprocessing_demo`).
    - В каждой карточке: `CTkLabel` id `card_title_{example_id}` и `CTkLabel` id `card_desc_{example_id}`.
  - В `content_frame`:
    - `CTkTextbox` id `output_text`.
    - `CTkButton` id `run_button`.
    - `CTkButton` id `clear_button`.
    - `CTkProgressBar` id `progressbar`.
    - `CTkLabel` id `status_label`.
  - Все цвета и `corner_radius` заданы в `.ui` согласно дизайн-спецификации.
- Шаги:
  1. Переписать `.ui` на классах `customtkinter.*`.
  2. Сохранить stable id виджетов для `application_window.py`.
  3. Убедиться, что XML валиден и Builder загружает файл.
- Checkpoint:
  ```bash
  uv run python -c "from pygubu import Builder; b = Builder(); b.add_from_file('ex_window_app_customtkinter/window_app.ui'); print('ui loaded')"
  ```
  Ожидание: exit 0, `.ui` загружен Builder'ом. Если Builder требует дисплей — fallback на `xvfb-run -a ...`.
- Готовность фазы: `.ui` валиден, Builder его принимает.

### Фаза 4: Оконный класс

- Файлы: `ex_window_app_customtkinter/application_window.py`.
- Контракт:
  - Класс `ApplicationWindow`.
  - GUI-объекты создаются только внутри `__init__`.
  - Используется `customtkinter.CTk` как окно; путь к `.ui` через `Path(__file__).with_name("window_app.ui")`.
  - Привязка виджетов по stable id из фазы 3.
  - Карточки примеров кликабельны: клик выделяет карточку и устанавливает `_selected_example_id`.
  - `search_entry` фильтрует видимость карточек по подстроке (case-insensitive).
  - Запуск примера — в `threading.Thread`, результат через `queue.Queue`, опрос через `window.after(100, self._poll_queue)`.
  - `progressbar` запускается/останавливается через `.start()` / `.stop()`.
  - `output_text` обновляется только из главного потока.
  - Импорт модуля не создаёт `CTk()` / `Tk()` на уровне модуля.
- Шаги:
  1. Заменить `ttkbootstrap` на `customtkinter`.
  2. Реализовать привязку карточек, фильтр, запуск в потоке, доставку вывода.
  3. Убрать переключатель тем ttkbootstrap.
  4. Обновить docstring'и.
- Checkpoint:
  ```bash
  uv run ruff check ex_window_app_customtkinter/
  uv run python -c "from ex_window_app_customtkinter.application_window import ApplicationWindow; print('import ok')"
  xvfb-run -a uv run python -m ex_window_app_customtkinter.main_window_app --smoke-window 5
  ```
  Ожидание: ruff без ошибок; импорт headless; smoke-window завершается сам с exit 0, без traceback.
- Готовность фазы: окно собирается, карточки и кнопки работают, smoke-window зелёный.

### Фаза 5: Точка входа

- Файлы: `ex_window_app_customtkinter/main_window_app.py`.
- Контракт:
  - Импорты и тексты помощи argparse обновлены под новое имя пакета.
  - `--smoke [name]` — headless, импортирует только `example_runner`, exit 0/2.
  - `--smoke-window [sec]` — создаёт `ApplicationWindow`, закрывает через `window.after(sec * 1000, ...)`, exit 0.
  - GUI-ветка — mainloop.
  - На уровне модуля не создаётся `Tk()`/`CTk()`.
- Шаги:
  1. Заменить имя пакета в импортах, prog argparse, docstring'ах.
  2. Сохранить логику CLI без изменений.
- Checkpoint:
  ```bash
  uv run ruff check ex_window_app_customtkinter/
  uv run python -m ex_window_app_customtkinter.main_window_app --smoke valid_bracket
  xvfb-run -a uv run python -m ex_window_app_customtkinter.main_window_app --smoke-window 3
  ```
  Ожидание: ruff без ошибок; `--smoke` выводит результат проверки скобок; smoke-window завершается за ~3 секунды с exit 0.
- Готовность фазы: headless и windowed smoke работают.

### Фаза 6: Документация

- Файлы: `docs/01_project_structure.md`, `docs/02_examples_overview.md`.
- Контракт:
  - В `01_project_structure.md` заменить `ex_window_app_ttkbootstrap` на `ex_window_app_customtkinter` в дереве и списке зависимостей; описать `customtkinter` вместо `ttkbootstrap`.
  - В `02_examples_overview.md` заменить имя пакета и команды запуска, обновить описание (CustomTkinter, карточки, сайдбар).
- Шаги:
  1. Заменить имя пакета в обоих файлах.
  2. Обновить описание GUI-примера.
- Checkpoint:
  ```bash
  grep -q "ex_window_app_customtkinter" docs/01_project_structure.md
  grep -q "ex_window_app_customtkinter/main_window_app.py" docs/02_examples_overview.md
  grep -q "customtkinter" docs/01_project_structure.md
  ! grep -q "ex_window_app_ttkbootstrap" docs/01_project_structure.md
  ! grep -q "ex_window_app_ttkbootstrap" docs/02_examples_overview.md
  ```
  Ожидание: все команды grep возвращают 0.
- Готовность фазы: документация отражает новый пакет.

## Критерии успеха

Проверяются qa по завершении всех фаз; сырые выводы — в `tasks/current/e2e/`.

| # | Критерий | Проверка | Ожидание |
|---|---|---|---|
| 1 | Runtime-зависимости переключены | `uv run python -c "import customtkinter as ctk, pygubu; print(ctk.__version__, pygubu.__version__)"` | exit 0, `ttkbootstrap` не импортируется и не в `pyproject.toml` |
| 2 | Ruff чист по новому пакету | `uv run ruff check ex_window_app_customtkinter/` | нет ошибок |
| 3 | Пакет переименован | `ls ex_window_app_customtkinter/` + `grep -R "ex_window_app_ttkbootstrap" ex_window_app_customtkinter/` | каталог существует, старое имя не найдено |
| 4 | Раннер запускает пример headless | `uv run python -m ex_window_app_customtkinter.main_window_app --smoke valid_bracket` | вывод содержит результат проверки скобок, exit 0 |
| 5 | `.ui`-файл валиден | `uv run python -c "from pygubu import Builder; b=Builder(); b.add_from_file('ex_window_app_customtkinter/window_app.ui')"` | exit 0; при необходимости — под `xvfb-run -a` |
| 6 | Импорт GUI-модуля не создаёт окно на уровне модуля | `uv run python -c "from ex_window_app_customtkinter.application_window import ApplicationWindow; print('import ok')"` | exit 0, `CTk()` не создаётся при импорте |
| 7 | Дизайн-требования в коде | grep-проверки по `application_window.py` + `window_app.ui` | присутствуют `corner_radius`, `set_appearance_mode("Dark")`, `set_default_color_theme("blue")`, акцентный цвет `#3b8ed0` |
| 8 | Окно собирается и закрывается под Xvfb | `xvfb-run -a uv run python -m ex_window_app_customtkinter.main_window_app --smoke-window 5` | exit 0, traceback в выводе нет |
| 9 | Документация обновлена | grep в `docs/` | присутствуют `ex_window_app_customtkinter` и команда запуска, отсутствует `ex_window_app_ttkbootstrap` |

## Финальные критерии

1. Каждый критерий успеха подтверждён доказательством (e2e/, DEFECTS.md, ADVERSARIAL_REVIEW.md).
2. `tasks/current/DEFECTS.md` существует только если найдены дефекты; все записи не OPEN.
3. Adversarial-прогон выполнен, ни одна запись ADVERSARIAL_REVIEW.md не PENDING.

## Открытые вопросы

Открытых вопросов нет: тема (статично Dark), выбор примера (только карточки) и
палитра (зафиксирована) закрыты решениями пользователя 2026-09-09 и перенесены
в «Подтверждённые решения».
