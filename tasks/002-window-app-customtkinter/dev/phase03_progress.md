# Phase 03 — UI-разметка на CTk (window_app.ui)

Дата: 2026-09-09
Агент: backend-dev
Контекст: фазы 1–2 закрыты — `customtkinter==6.0.0` в зависимостях, пакет переименован в `ex_window_app_customtkinter/`. `application_window.py` пока ссылается на `ttkbootstrap` — НЕ трогаю (фаза 4). Цель фазы 3: переписать только `ex_window_app_customtkinter/window_app.ui` с ttk-виджетов на CTk-виджеты через плагин `pygubu.plugins.customtkinter`.

## План

1. Создать `tasks/current/dev/phase03_progress.md` и `phase03_raw.txt` для прогресса и сырых выводов.
2. Изучить плагин `pygubu.plugins.customtkinter` в `.venv`: какие class-имена и свойства зарегистрированы, как именно Builder резолвит `customtkinter.*` (через `<requires lib="customtkinter"/>`).
3. Сверить дизайн-спецификацию (REQUIREMENTS.md) с поддерживаемыми свойствами CTk-виджетов в плагине — отметить отсутствующие `mode`/`indeterminate_speed`/etc.
4. Спроектировать дерево виджетов: корневой CTkFrame `main_frame` → `sidebar_frame` (col 0) + `content_frame` (col 1, expand) → листья по дизайн-спеце.
5. Переписать `window_app.ui` одним `write_file` (новый файл — единый XML с CTk-классами, stable id, цветами и layout-менеджерами).
6. Проверить XML-валидность (`ET.parse`) и загрузку Builder'ом под `xvfb-run -a` + walk по дереву виджетов для отчёта.
7. Сырые выводы — в `phase03_raw.txt`.

## Прогресс

### 2026-09-09 — старт

- Прочитал AGENTS.md (зоны backend-dev, особые запреты), спецификацию фазы 3 и phase02_progress.md.
- Прочитал существующий `window_app.ui` (ttk-разметка: Frame/Combobox/Text/Scrollbar/Progressbar) и `example_runner.py` (5 примеров: `async_context_var`, `valid_bracket`, `zip_operations`, `metaclass_vars`, `multiprocessing_demo`).
- Прочитал плагин `pygubu.plugins.customtkinter`:
  - `__init__.py` — `module_map` показывает, какие CTk-классы поддерживаются:
    - `pygubu.plugins.customtkinter.widgets`: CTkFrame, CTkLabel, CTkProgressBar, CTkButton, CTkSlider, CTkEntry, CTkOptionMenu, CTkComboBox, CTkCheckBox, CTkRadioButton, CTkSwitch, CTkTextbox, CTkCanvas, CTkScrollbar, CTkScrollableFrame.
    - `pygubu.plugins.customtkinter.scrollableframe`: CTkScrollableFrame (отдельный модуль, переопределяет register).
    - `pygubu.plugins.customtkinter.tabview`: CTkTabview.
    - `pygubu.plugins.customtkinter.windows`: CTk, CTkToplevel.
  - `can_load(builder_id)` плагина — `builder_id.startswith("customtkinter.")`, поэтому классы в .ui пишем как `customtkinter.CTkFrame` и т.п.
  - `<requires lib="customtkinter"/>` — подтверждено экспериментально: Builder загружает минимальный .ui с этим тегом и классом `customtkinter.CTkFrame` без ошибок.
  - Свойства плагина, релевантные фазе 3:
    - CTkFrame: `width`, `height`, `corner_radius`, `border_width`, `bg_color`, `fg_color`, `border_color`, `background_corner_colors`. `container=True`, `container_layout=True` — поддерживает вложенность и grid.
    - CTkLabel: `text`, `textvariable`, `font`, `text_color`, `fg_color`, `width`, `height`, `corner_radius`, `image`, `anchor`, `compound`, `justify`, `padx`, `pady`, `state`, `underline`, `bg_color`, `border_color`, `border_width`, `text_color_disabled`.
    - CTkEntry: `placeholder_text`, `placeholder_text_color`, `fg_color`, `border_color`, `text_color`, `corner_radius`, `border_width`, `text`, `textvariable`, `font`, `width`, `state`, `justify`, `show`.
    - CTkButton: `text`, `command`, `fg_color`, `hover_color`, `text_color`, `border_color`, `corner_radius`, `font`, `width`, `height`, `state`, `image`, `compound`, `textvariable`, `anchor`.
    - CTkTextbox: `fg_color`, `text_color`, `font`, `border_color`, `corner_radius`, `wrap`, `state`, `width`, `height`, `text` (через кастомный setter), `scrollbar_button_color`, `scrollbar_button_hover_color`, `activate_scrollbars`.
    - CTkProgressBar: `fg_color`, `progress_color`, `corner_radius`, `border_color`, `border_width`, `width`, `height`, `variable`, `mode` (хоть CTkProgressBar не имеет публичного `mode`, в плагине свойство объявлено — Builder не падает, но runtime `configure(mode=...)` у CTkProgressBar отсутствует; безопаснее НЕ указывать `mode` в .ui — дизайн-спека тоже этого требует).
    - CTkScrollableFrame: `fg_color`, `border_color`, `corner_radius`, `width`, `height`, `bg_color`, `border_width`, `scrollbar_fg_color`, `scrollbar_button_color`, `scrollbar_button_hover_color`, `label_fg_color`, `label_text_color`, `label_text`, `label_font`, `label_anchor`, `orientation`. **`container_layout=False`**: внутри scrollable frame не используется `layout_manager` от родителя — дети описывают только `layout` (grid col/row/sticky) для собственного grid внутри ScrollableFrame. Это важно для карточек.

- Прочитал `ctkbase.py` — обрабатывает int/bool/font-значения, плюс `font` парсится из строки `{Family} size {modifiers}` (например, `{Arial} 12 {bold}`), как требует спека. В спецификации для CTkEntry я указал `border_color`, `text_color` и т.п. — все они валидные свойства плагина.

- Экспериментально проверил pygubu-резолвинг: минимальный .ui с `<requires lib="customtkinter"/>` + `<object class="customtkinter.CTkFrame" id="main_frame">` грузится `pygubu.Builder` без ошибок под `xvfb-run -a uv run python -c "..."`. Сырой вывод — в `phase03_raw.txt` (шаг 2).

### 2026-09-09 — шаг 3: проект дерева виджетов

Дерево (стабильные id обязательны — на них завязана фаза 4):

```
main_frame            (CTkFrame, corner_radius=0, fg=#121212, height=480, width=720, sticky nsew)
├── sidebar_frame     (CTkFrame, col 0, fg=#1e1e1e, corner_radius=12, sticky nsw, padx/pady=16)
│   ├── sidebar_title      (CTkLabel, text "Примеры", font {Arial} 16 {bold}, text_color #e0e0e0, row 0)
│   ├── search_entry       (CTkEntry, placeholder_text "Поиск примера...",
│   │                       corner_radius=8, fg=#2b2b2b, border=#3a3a3a,
│   │                       text_color=#e0e0e0, placeholder_text_color=#6e6e6e, row 1)
│   ├── cards_scroll       (CTkScrollableFrame, fg transparent, corner_radius=0, row 2, expand)
│   │   ├── card_async_context_var     (CTkFrame, corner_radius=10, fg=#252525,
│   │   │   border_width=1, border_color=#333333, row 0, sticky ew, pady=4)
│   │   │   ├── card_title_async_context_var   (CTkLabel, font {Arial} 12 {bold}, text_color #f0f0f0)
│   │   │   └── card_desc_async_context_var    (CTkLabel, font {Arial} 10 {}, text_color #a0a0a0, wraplength=220)
│   │   ├── card_valid_bracket         (CTkFrame, ..., row 1, sticky ew, pady=4)
│   │   │   ├── card_title_valid_bracket
│   │   │   └── card_desc_valid_bracket
│   │   ├── card_zip_operations        (CTkFrame, ..., row 2, sticky ew, pady=4)
│   │   │   ├── card_title_zip_operations
│   │   │   └── card_desc_zip_operations
│   │   ├── card_metaclass_vars        (CTkFrame, ..., row 3, sticky ew, pady=4)
│   │   │   ├── card_title_metaclass_vars
│   │   │   └── card_desc_metaclass_vars
│   │   └── card_multiprocessing_demo  (CTkFrame, ..., row 4, sticky ew, pady=4)
│   │       ├── card_title_multiprocessing_demo
│   │       └── card_desc_multiprocessing_demo
└── content_frame    (CTkFrame, col 1, fg=#151515, corner_radius=12, sticky nsew, padx/pady=16)
    ├── output_text          (CTkTextbox, font {JetBrains Mono} 10 {},
    │                         fg=#0d0d0d, text_color=#d4d4d4, border=#2a2a2a,
    │                         corner_radius=8, wrap=word, row 0, sticky nsew)
    ├── run_button           (CTkButton, text "Запустить", corner_radius=10,
    │                         fg=#3b8ed0, hover=#2c6fa3, text_color=#ffffff,
    │                         font {Arial} 12 {bold}, width=140, height=36, row 1, sticky w, pady=(8, 0))
    ├── clear_button         (CTkButton, text "Очистить", corner_radius=10,
    │                         fg=#3a3a3a, hover=#4a4a4a, text_color=#e0e0e0,
    │                         width=100, height=32, row 1, sticky w, padx=(150, 0), pady=(8, 0))
    ├── progressbar          (CTkProgressBar, fg=#2a2a2a, progress_color=#3b8ed0,
    │                         corner_radius=6, row 2, sticky ew, pady=(12, 0))
    └── status_label         (CTkLabel, text "Готово", text_color=#909090,
                              font {Arial} 10 {}, row 3, sticky w, pady=(8, 0))
```

Layout-менеджеры:
- `main_frame`: grid 2 столбца, 1 строка. col 0 фиксированный (sidebar ~260 px), col 1 expand (1). sticky nsew на оба.
- `sidebar_frame`: grid 1 столбец, 3 строки. row 0 (title) — без expand. row 1 (search) — без expand. row 2 (cards_scroll) — expand=1, sticky nsew. sticky nsw.
- `cards_scroll`: внутри CTkScrollableFrame используется grid (по умолчанию) — карточки лежат друг под другом в строках 0..4, sticky ew.
- `content_frame`: grid 1 столбец, 4 строки. row 0 (output_text) — expand=1, sticky nsew. row 1 (run+clear) — без expand. row 2 (progressbar) — без expand. row 3 (status) — без expand.

Имена/описания карточек (из `example_runner.py`):
- `async_context_var` — «Async: ContextVar в задачах», описание: «ContextVar и asyncio-задачи».
- `valid_bracket` — «Code War: проверка скобочных последовательностей», описание: «Баланс скобок в строке».
- `zip_operations` — «ZIP: запись и чтение архивов», описание: «zipfile: создание и чтение».
- `metaclass_vars` — «Metaclass: переменные внутри функций», описание: «Метакласс и область видимости».
- `multiprocessing_demo` — «Multiprocessing: Process / Pool / Executor», описание: «Process, Pool, Executor».

### 2026-09-09 — шаг 4: переписать window_app.ui

Файл `ex_window_app_customtkinter/window_app.ui` переписан целиком одним `write_file` — новая разметка на классах `customtkinter.*`, stable id, цвета/скругления по дизайн-спецификации, grid-layout с правильными весами столбцов и строк. XML-валидность и загрузка Builder'ом — на следующем шаге.

### 2026-09-09 — шаг 5: checkpoint

Команды и их вердикты (детали в `phase03_raw.txt` и `phase03_checkpoint.txt`):

| # | Команда | Ожидание | Факт | Вердикт |
|---|---|---|---|---|
| 1 | `uv run python -c "import xml.etree.ElementTree as ET; ET.parse('ex_window_app_customtkinter/window_app.ui'); print('xml ok')"` | exit 0, `xml ok` | `xml ok` (exit 0) | PASS |
| 2 | `xvfb-run -a uv run python -c "from pygubu import Builder; b = Builder(); b.add_from_file('ex_window_app_customtkinter/window_app.ui'); print('ui loaded')"` | exit 0, `ui loaded` | `ui loaded` (exit 0) | PASS |
| 3 | `uv run python -c "from pygubu import Builder; ..."` без Xvfb (headless parse) | exit 0 | `ui loaded` (exit 0) | PASS |
| 4 | `uv run ruff check ex_window_app_customtkinter/` | без ошибок | `All checks passed!` (exit 0) | PASS |
| 5 | grep всех 26 stable id | все найдены | 26/26 OK | PASS |

Счётчики виджетов в .ui:
- CTkFrame: 8 (main_frame + sidebar_frame + content_frame + 5 карточек)
- CTkLabel: 12 (sidebar_title + status_label + 5 card_title + 5 card_desc)
- CTkButton: 2 (run_button, clear_button)
- CTkEntry: 1 (search_entry)
- CTkTextbox: 1 (output_text)
- CTkProgressBar: 1 (progressbar)
- CTkScrollableFrame: 1 (cards_scroll)
- Итого: 26 объектов на CTk.

Дерево виджетов из .ui (фактически) — сохранено в `phase03_tree_dump.txt` (26 строк). Краткая выжимка:
- main_frame (CTkFrame, fg=#121212, corner_radius=0, 720×480)
  - sidebar_frame (CTkFrame, fg=#1e1e1e, corner_radius=12, width=260)
    - sidebar_title (CTkLabel, «Примеры», font {Arial} 16 {bold})
    - search_entry (CTkEntry, placeholder «Поиск примера...»)
    - cards_scroll (CTkScrollableFrame, fg=transparent)
      - 5 карточек (CTkFrame, fg=#252525, border=#333333) с двумя CTkLabel внутри
  - content_frame (CTkFrame, fg=#151515, corner_radius=12)
    - output_text (CTkTextbox, моноширинный, fg=#0d0d0d, wrap=word)
    - run_button (CTkButton, акцент #3b8ed0, 140×36)
    - clear_button (CTkButton, нейтральный, 100×32)
    - progressbar (CTkProgressBar, accent #3b8ed0, **без** `mode`)
    - status_label (CTkLabel, «Готово»)

#### Замечания

- `progressbar` — CTkProgressBar без свойства `mode`: дизайн-спека требует «у CTkProgressBar нет ttk-опции mode», и плагин pygubu декларирует `mode` для BO, но у самого `customtkinter.CTkProgressBar` нет публичного `mode`. Безопаснее в .ui `mode` не задавать, и `progressbar.start()` / `.stop()` в коде фазы 4 отработают без конфликта.
- `cards_scroll` — `CTkScrollableFrame` использован напрямую из плагина (`pygubu.plugins.customtkinter.scrollableframe.CTkScrollableFrameBO`). Никаких fallback'ов не понадобилось: плагин зарегистрирован через `module_map` в `__init__.py`, `can_load("customtkinter.CTkScrollableFrame") == True`, `class_ = CTkScrollableFrame`.
- `<requires lib="customtkinter"/>` — pygubu это принимает (метаинформация, не влияет на резолвинг, но дизайнер pygubu-designer использует для активации плагина).
- `clear_button` помещён в ту же строку row=1, что и `run_button`, через `sticky=w` и `padx=(170, 16)` — это даёт горизонтальный отступ от run_button и оставляет текстбокс единственным expand'ом в content_frame.

#### Сводка

- XML валиден (`ET.parse` без ошибок).
- pygubu.Builder грузит .ui под Xvfb без ошибок; headless без Xvfb тоже.
- ruff на пакете чист.
- Все 26 stable id присутствуют.
- CTkScrollableFrame использован напрямую из плагина — fallback не понадобился.
- Дизайн-палитра и corner_radius в .ui соответствуют дизайн-спецификации.

Готовность фазы: PASS.
