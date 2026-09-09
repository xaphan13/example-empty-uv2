# Прогресс фазы 4 — Оконный класс

## Старт: 2026-09-09

## Задача

Переписать `ex_window_app_customtkinter/application_window.py` — класс
`ApplicationWindow` на CustomTkinter + pygubu Builder, с wiring'ом виджетов
из `window_app.ui`. Старый код на ttkbootstrap заменить целиком.

## План

1. Создать `application_window.py` (write_file) — класс `ApplicationWindow`:
   - `__init__` — тема, окно CTk, Builder, get_object по stable id,
     привязка карточек (click/hover), фильтр, запуск, очередь.
   - Хелперы: `_set_status`, `_append_output`, `_clear_output`,
     `_set_selected`, `_apply_card_appearance`, `_set_running`.
   - Обработчики: `_on_card_click`, `_on_card_enter`, `_on_card_leave`,
     `_on_search_changed`, `_on_run_clicked`, `_start_example`,
     `_run_in_worker`, `_poll_queue`, `_on_clear_clicked`, `_on_close`.
2. Проверить `uv run ruff check ex_window_app_customtkinter/`.
3. Проверить headless-импорт.
4. Проверить `--smoke-window 5` под `xvfb-run -a`.
5. Точечно поправить `main_window_app.py`, если рассинхрон API.

## Ход

| Шаг | Файл | Статус | Проверки |
|-----|------|--------|----------|
| 1   | application_window.py | написан | ruff ✓, headless import ✓ |
| 2   | smoke-window под Xvfb | FAILED | ModuleNotFoundError: PIL — см. секцию «Блокер» |

## Блокер

`xvfb-run -a uv run python -m ex_window_app_customtkinter.main_window_app --smoke-window 5` падает на
`builder.get_object("main_frame", self.window)`:

```
File ".../pygubu/plugins/customtkinter/ctkbase.py", line 12, in <module>
    from PIL import Image, ImageTk
ModuleNotFoundError: No module named 'PIL'
```

Цепочка: `pygubu.builder._realize` → `pygubu.plugins.customtkinter.widgets`
→ `tabview` → `ctkbase` → `from PIL import Image, ImageTk`.

`Pillow` не установлен (`uv pip list | grep -i pillow` → пусто), не заявлен
в `pyproject.toml` и не вытянут транзитивно. На уровне `pygubu.Builder`
плагин customtkinter подключается автоматически (`import pygubu` →
`pygubu.plugins.__init__` генерирует реестр виджетов, не выполняя
импорт `widgets.py`). Но при первом `_realize` модуль `widgets.py`
импортируется впервые, и тут же `ctkbase` пытается импортировать PIL.

То есть:
- headless-импорт `from ex_window_app_customtkinter.application_window
  import ApplicationWindow` — работает, потому что виджеты не создаются.
- Builder загружает .ui через `add_from_file` — работает, потому что
  add_from_file парсит XML, но не резолвит классы (см. тестовый прогон
  фазы 3, чекпоинт `ui loaded`).
- `builder.get_object(...)` — падает, потому что это первое создание
  CTk-виджета, и плагин дотягивает PIL.

### Гипотеза
`Pillow` нужен только `tabview` (иконки вкладок) и, возможно, другим
виджетам плагина, но через `ctkbase` он импортируется в модуль-уровне,
поэтому падает независимо от того, какие виджеты реально используются.

### Варианты
1. Добавить `Pillow` в `[project].dependencies`. В спеке сказано
   «не добавлять зависимостей сверх customtkinter» — нужно явное решение
   оркестратора.
2. Если Pillow можно ограничить dev-группой — `pygubu` runtime
   его вроде бы не требует, это требование плагина customtkinter.
   Скорее всего всё-таки runtime, потому что виджеты плагина — это
   пользовательский код приложения.
3. Обходной манёвр в коде: установить `Pillow` условно / обмануть
   импорт (`sys.modules['PIL'] = types.ModuleType('PIL')` с фейковыми
   `Image`/`ImageTk`). Хрупко, не рекомендую.

Решение нужно от оркестратора. Прогон остановлен на границе:
`application_window.py` готов и проверен ruff/headless; smoke-window
не проходит из-за отсутствующего Pillow.

## Добивка после снятия блокера pillow: 2026-09-09

### Старт: 2026-09-09

#### Окружение
- `pillow==12.3.0` установлен (`uv pip list | grep -i pillow` — `pillow 12.3.0`).
  Импорт `from PIL import Image, ImageTk` отрабатывает штатно.
- `pygubu.plugins.customtkinter.ctkbase` теперь поднимается без
  `ModuleNotFoundError`. Блокер фазы 4 снят.
- Остаточных процессов после прошлого прогона нет (uvicorn и т.п.
  не поднимались; только headless и xvfb-run).

#### Прогон checkpoint-команд

| # | Команда | exit | Вердикт |
|---|---------|------|---------|
| 1 | `uv run ruff check ex_window_app_customtkinter/` | 0 | PASS — `All checks passed!` |
| 2 | `uv run python -c "from ex_window_app_customtkinter.application_window import ApplicationWindow; print('import ok')"` | 0 | PASS — `import ok` |
| 3 | `xvfb-run -a uv run python -m ex_window_app_customtkinter.main_window_app --smoke-window 5` | 0 | PASS (см. «Новый блокер → фикс» ниже) |

Бонусом (фаза 5, не в checkpoint фазы 4): `uv run python -m
ex_window_app_customtkinter.main_window_app --smoke valid_bracket`
— exit 0, вывод содержит результат проверки скобок.

#### Новый блокер (не pillow)

После снятия pillow smoke-window упал на новом месте:
```
_tkinter.TclError: bad pad value "(12,": must be positive screen distance
  File ".../pygubu/component/builderobject.py", line 301, in layout
    target.grid(**properties)
  File ".../customtkinter/.../ctk_base_class.py", line 321, in grid
    return super().grid(**self._apply_argument_scaling(kwargs))
```

##### Диагностика

1. `pady="(12, 8)"` в XML-разметке `.ui` (фаза 3, формат pygubu-дизайнера).
2. pygubu читает значение из XML как **строку** `"(12, 8)"` (см.
   `pygubu/component/uidefinition.py:273`, `meta.layout_properties[...]=p.text`)
   и кладёт в `layout_properties`.
3. При `_realize` → `parent.layout()` → `target.grid(**properties)` —
   `pady="(12, 8)"` уходит в tkinter.
4. CustomTkinter 5.x: `CTkBaseClass._apply_argument_scaling` проверяет
   `isinstance(pady, (int, float))` и `isinstance(pady, tuple)` — обе
   ветки **не срабатывают** для строки `"(12, 8)"`, значение пробрасывается
   в `tkinter.Tk.grid` без изменений.
5. Tcl/tkinter **не умеет** парсить `pady="(12, 8)"` как tuple: режет по
   запятой, теряет правую часть, оставляет висящий литерал `"(12,"`.
   Воспроизведено на чистом `tk.Label.grid(pady="(12, 8)")` —
   `TclError: bad pad value "(12,"`. Зато `pady="12 8"` и `pady=(12, 8)`
   работают штатно.

##### Решение (точечная правка `application_window.py`)

Добавлен статический метод `_patch_layout_pad_values` (вызывается
сразу после `builder.add_from_file(...)` в `__init__`). Метод
переписывает в памяти значения `<layout>/<property name="padx|pady">`
вида `(a, b[, c ...])` в формат `"a b"` (через пробел), который
Tcl/tkinter принимает нативно. XML-файл `window_app.ui` **не
трогается** (это разметка фазы 3, не входит в зону правки backend-dev
фазы 4) — изменения применяются только к копии дерева в памяти
(`builder.uidefinition.root` — ElementTree, общий объект с pygubu).

Точечный `edit` двух мест в `application_window.py`:
- вызов `self._patch_layout_pad_values(self.builder.uidefinition.root)`
  сразу после `add_from_file`, перед первым `get_object`;
- новый метод в начале секции «Управление состоянием UI» (название
  секции изменено на «Совместимость разметки» с комментарием).

Логика `ApplicationWindow` (привязка карточек, hover, поиск, запуск
в потоке, очередь, `after`) — не тронута.

##### Проверка фикса

| Команда | exit | Вывод |
|---|---|---|
| `uv run ruff check ex_window_app_customtkinter/` | 0 | `All checks passed!` |
| `uv run python -c "from ex_window_app_customtkinter.application_window import ApplicationWindow; print('import ok')"` | 0 | `import ok` |
| `xvfb-run -a uv run python -m ex_window_app_customtkinter.main_window_app --smoke-window 5` | 0 | exit 0, без traceback |

В выводе smoke-window присутствуют 5 warning'ов
`Attempt to set an unknown property 'wraplength' on class '<class 'customtkinter.windows.widgets.ctk_label.CTkLabel'>'`
— это особенность CustomTkinter 5.x (`CTkLabel` не поддерживает
`wraplength`), известная и **некритичная** (warning, не error).
`wraplength` задан в `.ui` для `card_desc_*` (5 карточек). Поскольку
`wraplength` — это **widget-свойство** CTkLabel, а не layout-свойство
grid'а, наш фикс padx/pady на это не распространяется. Возможные
варианты на будущее: убрать `wraplength` из `.ui` (фаза 3 / 6),
либо заменить на поддерживаемый аналог. Сейчас warning **не ломает
checkpoint** (exit 0, окно открывается и закрывается).

#### Лог-артефакты

Каталог `ex_window_app_customtkinter/log/` существует и содержит
`empty-uv2.log` (0 байт, создан `config_log.py`/рантаймом). Он
указан в `.gitignore` (`log/`, `*.log`), на прогон не влияет. В
прогоне smoke-window лог-файлы в этом каталоге не пишутся (это
`config_log` использует, но `application_window.py` его не вызывает
— `logF` импортируется только в других `ex_*`). Оставляем как есть.

#### Вердикт по фазе 4

Checkpoint фазы 4 — **зелёный**. Правки минимальны и локализованы в
`application_window.py` (одна точечная вставка вызова + один новый
статический метод). `.ui` не трогали, `main_window_app.py` не трогали.

#### Файлы этой добивки
- `ex_window_app_customtkinter/application_window.py` — добавлен
  вызов и метод `_patch_layout_pad_values` (+~70 строк с docstring).
- `tasks/current/dev/phase04_progress.md` — эта секция.
- `tasks/current/dev/phase04_raw.txt` — сырые выводы checkpoint'а.

