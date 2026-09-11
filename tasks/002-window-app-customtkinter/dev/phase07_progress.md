# Фаза 7 — Редизайн v2: заполненное окно (backend-dev)

Дата: 2026-09-09.
Зона: `ex_window_app_customtkinter/window_app.ui`, `ex_window_app_customtkinter/application_window.py`,
`../../../ex_window_app_customtkinter/main_window_ctk.py` (только docstring/--help), `tasks/current/dev/phase07_*`.

Контракт: см. раздел «Фаза 7: Редизайн v2 — заполненное окно» в
[tasks/current/REQUIREMENTS.md](../REQUIREMENTS.md). Шапка + опции + метрики
+ output + кнопки + прогресс + статус в контенте; палитра Tokyo Night;
grid-веса; свитчи «Очистка перед запуском» и «Автопрокрутка вывода»;
кнопка «Копировать»; метрики (реестр/последний запуск/статус);
search_counter в сайдбаре; окно 900x600 (minsize 800x520).

## План
1. `window_app.ui` — полностью переписать разметку: контент разбит на секции,
   сайдбар получил `search_counter`. Все id из спеки, цвета Tokyo Night.
2. `application_window.py` — обновить константы палитры/метрик, геометрию,
   добавить grid-веса, wiring новых виджетов, переработка логики шапки,
   copy_button, метрик и search_counter. Старая логика (выбор карточки,
   фильтр, threading+queue+after, progressbar) сохранена.
3. `main_window_ctk.py` — заменить упоминания ttkbootstrap на CustomTkinter
   в module docstring и argparse help.

## Прогресс

### Шаг 2 — application_window.py (сделан, 2026-09-09)
- Импортирован `datetime as _dt` для метки времени в `metric_last_run_value`.
- Палитра вынесена в константы уровня модуля с префиксом `_COLOR_*`
  (акцент `#7aa2f7`/`#89b4fa`, карточки `#292e42`/`#3b4261`/`#363e59`,
  выбранная `#2f334d`/`#7aa2f7`, тексты `#c0caf5`/`#e8ecfd`/`#565f89`,
  метрики `#7dcfff`/`#9ece6a`/`#c0caf5`, ошибка `#f7768e`).
- Окно: `900x600`, `minsize=(800, 520)`.
- Grid-веса и позиции задаются **кодом** после `get_object`,
  надёжнее .ui (фаза 7 спека): `main_frame.columnconfigure(0, weight=0)`,
  `columnconfigure(1, weight=1)`, `rowconfigure(0, weight=1)`. Затем
  `sidebar_frame.grid_configure(row=0, column=0, sticky="nsew", padx=12, pady=12)`
  и `content_frame.grid_configure(row=0, column=1, sticky="nsew", padx=12, pady=12)`.
  Без явной расстановки `row/column` pygubu кладёт оба в одну
  колонку (`row=0,col=0`) и (`row=1,col=0`) — это поймано геометрической
  самопроверкой и исправлено.
- Внутри `sidebar_frame` строки 0/1/2 (title/search_entry/search_counter)
  имеют `weight=0`, строка 3 (`cards_scroll`) — `weight=1`.
- Внутри `content_frame` строки 0/1/2/4/5/6 — `weight=0`, строка 3
  (`output_text`) — `weight=1`.
- Привязка новых виджетов: `example_title`/`example_desc` (шапка),
  `clear_before_run_switch`/`autoscroll_switch` (опции),
  `metric_registry_value`/`metric_last_run_value`/`metric_status_value` (метрики),
  `search_counter` (счётчик), `copy_button` (копирование).
- Свитчи: `select()` в `__init__` — оба по умолчанию on, как требует спека.
- Метрика «реестр»: `metric_registry_value` заполняется из `len(examples)`
  при инициализации (5).
- Метрика «последний запуск»: обновляется в `_update_last_run_metric` —
  формат «title (HH:MM:SS)». Использует `datetime.now()`.
- Метрика «статус»: обновляется в `_set_metric_status` цветом —
  `#f7768e` для ошибки, `#c0caf5` для остальных.
- `search_counter` обновляется в `_on_search_changed` —
  «Найдено: N из 5» после фильтрации.
- `example_title`/`example_desc` обновляются в `_update_header` при
  клике по карточке; источник текстов — `_EXAMPLE_DESCRIPTIONS`.
- Свитч «Очистка перед запуском» управляет `_clear_before_run_enabled()`
  в `_on_run_clicked`: если on, `output_text` очищается перед стартом.
- Свитч «Автопрокрутка вывода» управляет `_autoscroll_enabled()` в
  `_append_output`: если on, `output_text.see("end")` после `insert`.
- `_on_copy_clicked`: `_copy_output_to_clipboard()` через
  `clipboard_clear` + `clipboard_append`; статус «Вывод скопирован»
  при успехе, «Нечего копировать» при пустом выводе. `update_idletasks`
  форсирует обработку clipboard перед возможным `quit`.
- Сохранены прежние механики: клик по карточке (выбор + подсветка +
  заголовок), hover через Enter/Leave, фильтр поиска, threading+queue
  + `after(100)`, progressbar start/stop, состояние run_button,
  protocol("WM_DELETE_WINDOW").

### Шаг 3 — main_window_app.py (только тексты, 2026-09-09)
- Docstring модуля: `ttkbootstrap` → `customtkinter` в перечислении GUI-библиотек.
- `argparse` description: «GUI-примера на ttkbootstrap + pygubu» →
  «GUI-примера на CustomTkinter + pygubu».
- `__init__.py` пакета: «GUI-пример на ttkbootstrap + pygubu» →
  «GUI-пример на CustomTkinter + pygubu».
- CLI-семантика (`--smoke`, `--smoke-window`) не изменена.

## Проверки (checkpoint + самопроверка геометрии)

### Ruff
```
$ uv run ruff check ex_window_app_customtkinter/
All checks passed!
```

### Headless import
```
$ uv run python -c "from ex_window_app_customtkinter.application_window import ApplicationWindow; print('import ok')"
import ok
```

### Smoke headless
```
$ uv run python -m ex_window_app_customtkinter.main_window_app --smoke valid_bracket
2026-09-09 18:37:47 [INFO] OnlyFile: '****' main_code_war - 'start'
2026-09-09 18:37:47 [INFO] OnlyFile: '****' run_valid - 'start'
2026-09-09 18:37:47 [INFO] OnlyFile: inn() - res = (True, '({[]})')
2026-09-09 18:37:47 [INFO] OnlyFile: inn() - res = (True, '({[]})')
2026-09-09 18:37:47 [INFO] OnlyFile: inn() - res = (False, '[', '(')
exit 0
```

### Smoke window under Xvfb
```
$ xvfb-run -a uv run python -m ex_window_app_customtkinter.main_window_app --smoke-window 5
exit 0
# stdout: пусто (как и положено — окно без вывода до запуска примера)
# stderr: пусто (нет tk-warning'ов, нет traceback)
```

### Самопроверка геометрии (адаптирована — после `update_idletasks()`/`update()`)
```
window:           900 x 600   ← ожидалось 900x600
main_frame:       900 x 600
sidebar:          233 x 576   ← высота 576 ≈ 600-24, sidebar растянут по вертикали
search_counter:   126 x 28
cards_scroll:     200 x 430   ← внутри sidebar, растягивается
content:          619 x 576   ← растягивается на всю высоту/ширину
header:           579 x 58    ← шапка внутри content
options:          579 x 24    ← панель свитчей
metrics:          579 x 74    ← три мини-карточки на одной строке
output_text:      579 x 292   ← > 200, растягивается (weight=1)
buttons:          579 x 36    ← три кнопки в ряд
progressbar:      579 x 8
status_label:     ...
```
Сравнение с v1 (диагноз оркестратора): main_frame был 760x540, sidebar 233x292,
content 304x328. Сейчас main_frame 900x600, sidebar 233x576, content 619x576,
output_text 579x292 — все секции растянулись, веса работают.

### Скриншот
`tasks/current/screenshots/phase07_window_v2.png` (900x600) — подтверждает
визуально: окно заполнено элементами, палитра Tokyo Night, hover на
первой карточке, все секции (шапка/опции/метрики/output/кнопки/прогресс/статус)
на своих местах, sidebar занимает всю высоту окна.

## Замечания по контракту
- `search_entry.configure(textvariable=self._search_var)` использует
  `tk.StringVar` (а не `CTkVariable`) — это работает в текущей версии
  CTk и совместимо со `trace_add`. Если в будущей версии CTk сменит
  API — точечная правка в `_search_var` (без изменения остального кода).
- `clear_before_run_switch.select()` и `autoscroll_switch.select()` задают
  on-состояние по умолчанию; в .ui свойство `onvalue`/`offvalue` не задано,
  поэтому состояние on = 1, что совпадает с инт-проверкой в
  `_autoscroll_enabled()` / `_clear_before_run_enabled()`. Если поведение
  CTkSwitch изменится в будущей версии (например, `get()` начнёт
  возвращать bool), адаптеры `_autoscroll_enabled` / `_clear_before_run_enabled`
  упадут в ветку `return bool(value)` — это безопасный fallback.
- Скриншот сделан с hover-эффектом на первой карточке (мышь в области
  карточки) — это не выбранное состояние, просто hover. Подсветка выбора
  рисуется с другим цветом (`#2f334d`/`#7aa2f7`) и включается только
  после клика.

