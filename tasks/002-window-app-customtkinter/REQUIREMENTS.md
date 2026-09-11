# Перевод GUI-примера с ttkbootstrap на CustomTkinter (задание 002)

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
- `main_window_ctk.py` не меняет семантики: `--smoke [name]` (headless, exit 0/2) и `--smoke-window [sec]` (окно + автозакрытие через `after`) сохраняются с теми же аргументами.
- Дизайн-требования жёстко зафиксированы в спеке: тёмная тема, скругления, акцент, отступы, hover — см. раздел «Дизайн-спецификация».
- `main.py` не трогать; другие `ex_*` не трогать; тесты не писать; новых GUI-библиотек кроме `customtkinter` не добавлять. Исключение — `pillow`: обязательное требование плагина `pygubu.plugins.customtkinter` (безусловный `from PIL import ...` на уровне модуля `ctkbase.py`); до этого задания pillow присутствовал в `uv.lock` транзитивно через `ttkbootstrap` и был удалён вместе с ним в фазе 1 — решение оркестратора от 2026-09-09: `pillow` добавлен как прямая runtime-зависимость.

## Результат

После задания в репозитории должны существовать:

- `pyproject.toml` / `uv.lock` с `customtkinter` и `pillow` в runtime-зависимостях, без `ttkbootstrap`; `pygubu` и `pygubu-designer` остаются.
- Пакет `ex_window_app_customtkinter/` (переименованный из `ex_window_app_ttkbootstrap`):
  - `__init__.py` — маркер пакета с новым именем.
  - `main_window_ctk.py` — точка входа, парсит `--smoke [name]` / `--smoke-window [sec]`, лениво импортирует GUI.
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
- Не добавлять зависимостей сверх `customtkinter` и `pillow` (обоснование pillow — в «Подтверждённых решениях»).
- Не поддерживать запуск примеров вне реестра.

## Дизайн-спецификация

### Общая раскладка

> Редизайн v2 (требование пользователя от 2026-09-09 после ревью v1): окно не должно
> быть пустым — элементы управления заполняют всю площадь, цвета контрастные, различимые.
> Первая версия сжала виджеты в угол из-за отсутствия grid-весов.

- Корневое окно создаётся программно в `application_window.py`: `ctk.CTk()` после `ctk.set_appearance_mode("Dark")` и `ctk.set_default_color_theme("blue")`. Корневой объект `.ui` — `CTkFrame` id `main_frame`, он встраивается в окно через `pack(fill="both", expand=True)`.
- **Grid-веса обязательны** (настраиваются кодом в `application_window.py` после `get_object`, надёжнее pygubu-layout):
  - `main_frame.columnconfigure(0, weight=0)` — сайдбар фикс. ширина; `columnconfigure(1, weight=1)` — контент растягивается; `rowconfigure(0, weight=1)`.
  - Внутри `sidebar_frame`: строки заголовка/поиска/счётчика weight=0, строка `cards_scroll` weight=1.
  - Внутри `content_frame`: строки шапки/опций/метрик/кнопок/статуса weight=0, строка `output_text` weight=1.
- `main_frame` — `CTkFrame` с `fg_color="#1a1b26"`, `corner_radius=0`, растянут на всё окно.
- `main_frame` разбит на два столбца grid:
  - **Сайдбар** (`CTkFrame` id `sidebar_frame`, ширина фиксированная 280 px): `fg_color="#16161e"`, `corner_radius=12`.
  - **Контент** (`CTkFrame` id `content_frame`, weight=1): `fg_color="#1f2335"`, `corner_radius=12`.
- Отступы (padx/pady) — 12–16 px между сайдбаром и контентом, 8–10 px внутри секций. Формат составных отступов в `.ui` — `a b` через пробел (tkinter не парсит `(a, b)`).

### Сайдбар

- Заголовок `CTkLabel` id `sidebar_title`: текст «Примеры», шрифт `{Arial} 16 {bold}`, `text_color="#7aa2f7"` (акцент).
- Поле поиска `CTkEntry` id `search_entry`: `placeholder_text="Поиск примера..."`, `corner_radius=8`, `fg_color="#292e42"`, `border_color="#3b4261"`, `text_color="#c0caf5"`, `placeholder_text_color="#565f89"`.
- Счётчик `CTkLabel` id `search_counter`: текст «Найдено: 5 из 5», шрифт `{Arial} 10 {}`, `text_color="#565f89"`, обновляется кодом при фильтрации.
- Список карточек — `CTkScrollableFrame` id `cards_scroll`: `fg_color="transparent"`, `corner_radius=0`.
- Каждая карточка — `CTkFrame` id `card_{example_id}` (5 штук), `corner_radius=10`, `fg_color="#292e42"`, `border_width=1`, `border_color="#3b4261"`:
  - `CTkLabel` id `card_title_{example_id}` — заголовок примера, шрифт `{Arial} 12 {bold}`, `text_color="#c0caf5"`.
  - `CTkLabel` id `card_desc_{example_id}` — однострочное описание, шрифт `{Arial} 10 {}`, `text_color="#565f89"` (без `wraplength`: pygubu применяет свойства через `configure()`, который не маршрутизирует `wraplength` на CTkLabel).
  - Карточка кликабельна: через `bind("<Button-1>", ...)` в `application_window.py` выбирает пример.
  - Hover-эффект карточки: `fg_color="#363e59"` через `bind("<Enter>")` / `bind("<Leave>")`.
  - Выбранная карточка: `border_color="#7aa2f7"`, `fg_color="#2f334d"`.

### Контент

- **Шапка** (вверху контента):
  - `CTkLabel` id `example_title`: текст «Выберите пример», шрифт `{Arial} 20 {bold}`, `text_color="#e8ecfd"`; при выборе карточки — название примера.
  - `CTkLabel` id `example_desc`: описание выбранного примера (2–3 строки), шрифт `{Arial} 11 {}`, `text_color="#565f89"`.
- **Панель опций запуска** (`CTkFrame` id `options_frame`, `fg_color="transparent"`):
  - `CTkSwitch` id `clear_before_run_switch`: text «Очистка перед запуском», `text_color="#c0caf5"`, `progress_color="#7aa2f7"`, по умолчанию on.
  - `CTkSwitch` id `autoscroll_switch`: text «Автопрокрутка вывода», аналогичные цвета, по умолчанию on.
- **Ряд метрик** (`CTkFrame` id `metrics_frame`, `fg_color="transparent"`): три мини-карточки `CTkFrame` (`metric_card_registry`, `metric_card_last_run`, `metric_card_status`), каждая `fg_color="#292e42"`, `corner_radius=10`, `border_width=1`, `border_color="#3b4261"`:
  - `metric_registry_label` — «Примеров в реестре», значение `metric_registry_value` — «5» (`{Arial} 16 {bold}`, `text_color="#7dcfff"`).
  - `metric_last_run_label` — «Последний запуск», значение `metric_last_run_value` — «—» (`text_color="#9ece6a"`), обновляется кодом (название примера + время).
  - `metric_status_label` — «Статус», значение `metric_status_value` — «Готово» (`text_color="#c0caf5"`).
- Панель вывода `CTkTextbox` id `output_text`: `font="{JetBrains Mono} 10 {}"`, `fg_color="#101017"`, `text_color="#c0caf5"`, `border_color="#3b4261"`, `corner_radius=8`, `wrap="word"`, занимает основную площадь (weight=1).
- **Панель кнопок** (`CTkFrame` id `buttons_frame`, `fg_color="transparent"`):
  - Кнопка «Запустить» `CTkButton` id `run_button`: `corner_radius=10`, `fg_color="#7aa2f7"`, `hover_color="#89b4fa"`, `text_color="#1a1b26"`, `font="{Arial} 12 {bold}"`, `width=140`, `height=36`.
  - Кнопка «Очистить» `CTkButton` id `clear_button`: `corner_radius=10`, `fg_color="#292e42"`, `hover_color="#363e59"`, `text_color="#c0caf5"`, `width=100`, `height=32`.
  - Кнопка «Копировать» `CTkButton` id `copy_button`: `corner_radius=10`, `fg_color="#292e42"`, `hover_color="#363e59"`, `text_color="#c0caf5"`, `width=120`, `height=32` — копирует содержимое output_text в буфер обмена (`clipboard_clear` + `clipboard_append`), статус подтверждает.
- Прогресс-индикатор `CTkProgressBar` id `progressbar`: `fg_color="#292e42"`, `progress_color="#7aa2f7"`, `corner_radius=6`. Анимация — `.start()` / `.stop()`.
- Статусная строка `CTkLabel` id `status_label`: `text="Готово"`, `text_color="#565f89"`, `font="{Arial} 10 {}"`.

### Цветовая палитра (Tokyo Night)

- Фон окна: `#1a1b26`. Сайдбар: `#16161e`. Контент: `#1f2335`.
- Карточки/мини-карточки: `#292e42`, бордюр `#3b4261`, hover `#363e59`.
- Выбранная карточка: `#2f334d` + бордюр `#7aa2f7`.
- Акцент: `#7aa2f7` (кнопка запуска, прогресс, заголовок сайдбара, свитчи, выделение). Акцент hover: `#89b4fa`.
- Метрики: голубой `#7dcfff`, зелёный `#9ece6a`, ошибка `#f7768e`.
- Текст основной: `#c0caf5`. Текст яркий: `#e8ecfd`. Вторичный: `#565f89`.
- Терминал (вывод): `#101017` / `#c0caf5`.
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
| 5 | Точка входа | backend-dev | `../../ex_window_app_customtkinter/main_window_ctk.py` | переименование импортов/текстов; `--smoke` и `--smoke-window` с прежней семантикой | ruff; `--smoke valid_bracket`; `--smoke-window 5` | ~10 |
| 6 | Документация | backend-dev | `docs/01_project_structure.md`, `docs/02_examples_overview.md` | новое имя пакета, команда запуска, описание CustomTkinter | grep нового имени и команды | ~6 |
| 7 | Редизайн v2: заполненное окно | backend-dev | `window_app.ui`, `application_window.py`, `main_window_ctk.py` (тексты --help) | grid-веса, шапка/опции/метрики/кнопки по всему окну, палитра Tokyo Night; см. дизайн-спецификацию v2 | ruff; smoke-window под Xvfb; скриншот-проверка заполненности | ~15 |

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
  uv run python -c "import customtkinter, pygubu; from importlib.metadata import version; print(customtkinter.__version__, version('pygubu'))"
  ```
  Ожидание: обе библиотеки импортируются, версии напечатаны, exit 0 (у pygubu нет атрибута `__version__`, версия читается через `importlib.metadata`).
- Готовность фазы: зависимости фиксированы, `ttkbootstrap` отсутствует в `pyproject.toml`/`uv.lock`.

### Фаза 2: Переименование пакета

- Файлы: весь каталог `ex_window_app_ttkbootstrap/` (5 файлов).
- Контракт:
  - `git mv ex_window_app_ttkbootstrap ex_window_app_customtkinter`.
  - Во всех `.py` заменить `ex_window_app_ttkbootstrap` на `ex_window_app_customtkinter` (импорты, docstring'и, тексты помощи argparse).
  - Логика `example_runner.py`, `application_window.py`, `main_window_ctk.py` не меняется — только переименование.
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

- Файлы: `../../ex_window_app_customtkinter/main_window_ctk.py`.
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

### Фаза 7: Редизайн v2 — заполненное окно

- Файлы: `ex_window_app_customtkinter/window_app.ui`, `ex_window_app_customtkinter/application_window.py`, `../../ex_window_app_customtkinter/main_window_ctk.py` (только тексты `--help`/docstring: убрать остатки упоминаний ttkbootstrap).
- Контракт:
  - `.ui`: новые секции контента — шапка (`example_title`, `example_desc`), панель опций (`options_frame`, `clear_before_run_switch`, `autoscroll_switch`), ряд метрик (`metrics_frame`, 3 мини-карточки), панель кнопок (`buttons_frame`, `run_button`, `clear_button`, `copy_button`); сайдбар дополняется `search_counter`. Палитра Tokyo Night по дизайн-спецификации v2.
  - `application_window.py`: grid-веса (сайдбар фикс, контент растягивается, output_text растягивается); wiring новых виджетов; свитчи управляют поведением (очистка перед запуском, автопрокрутка); «Копировать» — буфер обмена; метрики обновляются (реестр/последний запуск/статус); счётчик поиска.
  - `main_window_ctk.py`: только тексты помощи, без изменения CLI-семантики.
- Checkpoint:
  ```bash
  uv run ruff check ex_window_app_customtkinter/
  xvfb-run -a uv run python -m ex_window_app_customtkinter.main_window_app --smoke-window 5
  uv run python -m ex_window_app_customtkinter.main_window_app --smoke valid_bracket
  ```
  Ожидание: ruff чист; smoke-window exit 0 без traceback и без tk-warning'ов; smoke exit 0.
  Дополнительно оркестратор снимает скриншот под Xvfb и программно проверяет заполненность окна (несколько различимых цветов, контент во всех четвертях окна).
- Готовность фазы: окно заполнено элементами, палитра Tokyo Night, геометрия не сжимается.

## Критерии успеха

Проверяются qa по завершении всех фаз; сырые выводы — в `tasks/current/e2e/`.

| # | Критерий | Проверка | Ожидание |
|---|---|---|---|
| 1 | Runtime-зависимости переключены | `uv run python -c "import customtkinter, pygubu; from importlib.metadata import version; print(customtkinter.__version__, version('pygubu'))"` | exit 0, `ttkbootstrap` не импортируется и не в `pyproject.toml` |
| 2 | Ruff чист по новому пакету | `uv run ruff check ex_window_app_customtkinter/` | нет ошибок |
| 3 | Пакет переименован | `ls ex_window_app_customtkinter/` + `grep -R "ex_window_app_ttkbootstrap" ex_window_app_customtkinter/` | каталог существует, старое имя не найдено |
| 4 | Раннер запускает пример headless | `uv run python -m ex_window_app_customtkinter.main_window_app --smoke valid_bracket` | вывод содержит результат проверки скобок, exit 0 |
| 5 | `.ui`-файл валиден | `uv run python -c "from pygubu import Builder; b=Builder(); b.add_from_file('ex_window_app_customtkinter/window_app.ui')"` | exit 0; при необходимости — под `xvfb-run -a` |
| 6 | Импорт GUI-модуля не создаёт окно на уровне модуля | `uv run python -c "from ex_window_app_customtkinter.application_window import ApplicationWindow; print('import ok')"` | exit 0, `CTk()` не создаётся при импорте |
| 7 | Дизайн-требования в коде | grep-проверки по `application_window.py` + `window_app.ui` | присутствуют `corner_radius`, `set_appearance_mode("Dark")`, `set_default_color_theme("blue")`, акцентный цвет `#7aa2f7`, grid-веса (`columnconfigure`/`rowconfigure`), свитчи и метрики из v2 |
| 8 | Окно собирается и закрывается под Xvfb | `xvfb-run -a uv run python -m ex_window_app_customtkinter.main_window_app --smoke-window 5` | exit 0, traceback в выводе нет |
| 9 | Документация обновлена | grep в `docs/` | присутствуют `ex_window_app_customtkinter` и команда запуска, отсутствует `ex_window_app_ttkbootstrap` |

## Финальные критерии

1. Каждый критерий успеха подтверждён доказательством (e2e/, DEFECTS.md, ADVERSARIAL_REVIEW.md).
2. `tasks/current/DEFECTS.md` существует только если найдены дефекты; все записи не OPEN.
3. Adversarial-прогон выполнен, ни одна запись ADVERSARIAL_REVIEW.md не PENDING.

## Открытые вопросы

Открытых вопросов нет: тема (статично Dark), выбор примера (только карточки) и
палитра (зафиксирована) закрыты решениями пользователя 2026-09-09 и перенесены
в «Подтверждённые решения». В ходе исполнения контракт дважды уточнялся решениями
оркестратора (задокументированы в «Подтверждённых решениях» и дизайн-спецификации v2):
добавление `pillow` (требование плагина pygubu.plugins.customtkinter) и редизайн v2
после ревью пользователя (заполненное окно, палитра Tokyo Night, grid-веса).

---

# Отчёт о выполнении

- Дата закрытия: 2026-09-09
- Коммит: не коммитилось (изменения в рабочем дереве, ветка `task-new-custom`)

## Итог

GUI-пример переведён с ttkbootstrap на CustomTkinter: пакет переименован в
`ex_window_app_customtkinter`, окно (900×600) заполнено секциями (сайдбар карточек с
поиском и счётчиком, шапка, свитчи, метрики, «терминал», кнопки Запустить/Очистить/
Копировать, прогресс, статус) в палитре Tokyo Night; логика `example_runner.py`
не тронута; CLI-семантика `--smoke`/`--smoke-window` сохранена. Подтверждено
qa-прогоном 9/9 критериев (e2e/01–04) и перепроверкой дефектов (e2e/05).

## Изменения

- `pyproject.toml`, `uv.lock` → удалён `ttkbootstrap`, добавлены `customtkinter>=5.2.0` (6.0.0) и `pillow` (требование плагина pygubu.plugins.customtkinter).
- `ex_window_app_ttkbootstrap/` → `ex_window_app_customtkinter/` (git mv, 5 файлов).
- `window_app.ui` → полная разметка на CTk-виджетах (26 объектов v1 → 45 объектов v2), палитра Tokyo Night, padx/pady в формате `a b`.
- `application_window.py` → `ApplicationWindow` на CTk + pygubu Builder: grid-веса (сайдбар 280 px, контент растягивается), клик/hover/фильтр карточек, свитчи, метрики, копирование в буфер, threading+queue+after.
- `main_window_ctk.py` → тексты под CustomTkinter; `--smoke-window` валидирует строго положительные числа (DEF-003).
- `docs/01_project_structure.md`, `docs/02_examples_overview.md` → новый пакет, зависимости, описание UI v2.

## Критерии успеха

| # | Критерий | Результат | Доказательство |
|---|---|---|---|
| 1 | Runtime-зависимости переключены | PASS | e2e/01_static.txt (customtkinter 6.0.0, pygubu 0.42.1, ttkbootstrap=0) |
| 2 | Ruff чист по новому пакету | PASS | e2e/01_static.txt |
| 3 | Пакет переименован | PASS | e2e/01_static.txt (5 файлов, старое имя не найдено) |
| 4 | Раннер headless | PASS | e2e/02_runtime.txt (`--smoke valid_bracket`, exit 0) |
| 5 | `.ui` валиден | PASS | e2e/02_runtime.txt (`ui loaded`) |
| 6 | Импорт GUI-модуля без окна | PASS | e2e/02_runtime.txt (`import ok`) |
| 7 | Дизайн-требования в коде | PASS | e2e/03_design.txt (corner_radius=23, Dark/blue, #7aa2f7, weights, 5 id v2) |
| 8 | Окно под Xvfb, exit 0 | PASS | e2e/02_runtime.txt (stderr 0 байт); перепроверка после фиксов — e2e/05_defects.txt |
| 9 | Документация обновлена | PASS | e2e/04_docs_regress.txt (OK1–OK5) |

## Дефекты

Найдены adversary-прогоном, исправлены backend-dev, закрыты qa (e2e/05_defects.txt):
- DEF-001 (критичный): `progressbar.start(аргумент)` TypeError — запуск примера через GUI падал. CLOSED.
- DEF-002 (средний): сайдбар 233 px вместо 280 px. CLOSED (columnconfigure minsize=304 → 280 видимых).
- DEF-003 (средний): `--smoke-window -5/0` молча → 1 мс. CLOSED (argparse exit 2).

## Adversarial-прогон

7 записей, ни одной PENDING (ADVERSARIAL_REVIEW.md):
- ADV-001 → ACCEPTED -> DEF-001; ADV-006 → ACCEPTED -> DEF-001 (общий корень).
- ADV-002 → ACCEPTED -> DEF-002; ADV-007 → ACCEPTED -> DEF-002 (общий корень).
- ADV-004 → ACCEPTED -> DEF-003.
- ADV-003 → REJECTED (внутренний дефект CustomTkinter 6.0.0, не код продукта).
- ADV-005 → REJECTED (стандартное поведение argparse, работает как задумано).

## Участники

- backend-dev: фазы 1–7 (зависимости, переименование, .ui, оконный класс, точка входа, чистка техдолга, редизайн v2) + исправление DEF-001..003.
- qa: прогон 9 критериев + регресс (e2e/01–04), перепроверка и закрытие DEF-001..003 (e2e/05).
- adversary: враждебный прогон CLI/окна/гонок — 7 находок (ADVERSARIAL_REVIEW.md).
- оркестратор: ревью фаз, решение по pillow, триаж adversary, DEFECTS.md, редизайн-контракт v2 после ревью пользователя, скриншот-верификация, архивация.
