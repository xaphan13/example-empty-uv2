# Прогресс фазы 5 — Точка входа + чистка техдолга фазы 4

## Старт: 2026-09-09

## Задача

Две части:

**Часть A** — `main_window_app.py`: семантическая проверка после
переписывания `application_window.py` в фазе 4. CLI-логика
(`--smoke`/`--smoke-window`/mainloop) уже была переименована в фазе 2,
поэтому в этой фазе — только точечные правки вызовов API при
обнаруженном рассинхроне.

**Часть B** — чистка техдолга фазы 4 (решение оркестратора):

1. `ex_window_app_customtkinter/window_app.ui`:
   - 19 значений `padx`/`pady` в формате `"(a, b)"` → `"a b"`
     (пробел вместо скобок и запятой).
   - 5 строк `<property name="wraplength">220</property>` у
     `card_desc_*` — удалить.
2. `ex_window_app_customtkinter/application_window.py`:
   - Удалить статический метод `_patch_layout_pad_values` и его
     вызов из `__init__`. После правки `.ui` хак больше не нужен.

## План

1. `tasks/current/dev/phase05_progress.md` — `write_file`.
2. `window_app.ui` — `replace_all` для каждого уникального значения
   кортежа `(N, N)` → `N N`. 9 уникальных значений покрывают 19 строк.
3. `window_app.ui` — `replace_all` для строки
   `<property name="wraplength">220</property>` (5 одинаковых строк).
4. `application_window.py` — `edit`: удалить вызов метода и комментарий
   над ним в `__init__` (6 строк).
5. `application_window.py` — `edit`: удалить весь метод
   `_patch_layout_pad_values` вместе с секционным разделителем
   (один блок ~85 строк).
6. Checkpoint-команды и три grep-сверки.
7. Сырой вывод smoke-window — `tasks/current/dev/phase05_raw.txt`.

## Сверка исходного состояния

| Метрика | Значение | Источник |
|---|---|---|
| `<property name="(padx|pady)">\(N, N\)` | 19 строк | `grep -cE 'name="(padx|pady)">\(' window_app.ui` |
| `wraplength` | 5 строк | `grep -c wraplength window_app.ui` |
| `_patch_layout_pad_values` в `application_window.py` | 3 вхождения (комментарий, вызов, `def`) | `grep -c _patch_layout_pad_values application_window.py` |
| Кортежей `(N, N)` всего в `.ui` | 19 (= padx/pady) | `grep -cE '\([0-9]+, [0-9]+\)' window_app.ui` |

Последняя проверка важна: `replace_all` на каждом уникальном
значении кортежа безопасен, потому что все 19 вхождений `(N, N)` в
файле — это ровно те `padx`/`pady`, которые нужно заменить; других
скобочных кортежей в `.ui` нет.

## Ход

| Шаг | Файл | Действие | Проверки |
|-----|------|----------|----------|
| 1   | phase05_progress.md | создан | — |
| 2   | window_app.ui | `replace_all` 9 уникальных кортежей `(N, N)` → `N N` | grep -c `\(N, N\)` = 0 |
| 3   | window_app.ui | `replace_all` строки `wraplength` (5 одинаковых) | grep -c `wraplength` = 0 |
| 4   | application_window.py | `edit`: убрал вызов `self._patch_layout_pad_values(...)` + комментарий-пояснение (6 строк) | — |
| 5   | application_window.py | `edit`: убрал весь метод `_patch_layout_pad_values` + секционный разделитель «Совместимость разметки» | grep -c `_patch_layout_pad_values` = 0 |
| 6   | checkpoint-команды | ruff, smoke, smoke-window, headless import | см. таблицу ниже |

### Что правил в каждом файле

#### `window_app.ui`

- 9 `edit` (replace_all=true) по уникальным кортежам в padx/pady:
  - `(12, 8)` → `12 8` (1 шт.)
  - `(0, 8)` → `0 8` (2 шт.: search_entry, run_button, clear_button)
  - `(10, 2)` → `10 2` (5 шт.: card_title_*)
  - `(0, 10)` → `0 10` (5 шт.: card_desc_*)
  - `(16, 8)` → `16 8` (1 шт.: output_text)
  - `(16, 0)` → `16 0` (1 шт.: run_button)
  - `(170, 16)` → `170 16` (1 шт.: clear_button)
  - `(4, 4)` → `4 4` (1 шт.: progressbar)
  - `(0, 16)` → `0 16` (1 шт.: status_label)
  - **Итого: 19 строк.**
- 1 `edit` (replace_all=true) для удаления 5 одинаковых строк
  `<property name="wraplength">220</property>` у `card_desc_*`.
- Больше ничего в `.ui` не менял. `<property name="justify">left</property>`
  (тоже на card_desc_*) сохранён — `justify` не равен `wraplength`,
  на `wraplength` это никак не влияет.

#### `application_window.py`

- Удалил вызов `self._patch_layout_pad_values(self.builder.uidefinition.root)`
  в `__init__` (сразу после `self.builder.add_from_file(...)`) и
  комментарий-пояснение над ним (6 строк).
- Удалил весь метод `_patch_layout_pad_values` (~80 строк) вместе
  с секционным разделителем «Совместимость разметки». Секция
  «Управление состоянием UI» теперь идёт сразу после
  `__init__`-блока.
- **Ничего другого в классе не трогал**: ни bind'ы, ни hover, ни
  фильтр, ни воркер, ни очередь, ни прогресс, ни `_on_close`.
  Сигнатуры `__init__` / `self.window` / `_on_close()` — без изменений,
  рассинхрона с `main_window_app.py` нет.

#### `main_window_app.py`

Файл уже переименован в фазе 2 и не требовал правок в фазе 5
(часть A — сверка семантики, рассинхрона API не обнаружено):
- `ApplicationWindow()` — без аргументов, как и ожидается.
- `app.window` — атрибут окна, существует.
- `app._on_close()` — корректно завершает `mainloop` через
  `self.window.quit()`.
- `window.after(delay_ms, app._on_close)` — стандартный Tk-контракт.
- На уровне модуля импортируются только `argparse`, `sys`,
  `typing.Sequence` — никаких Tk/CTk-объектов.

## Checkpoint — все обязательные команды

| # | Команда | exit | Вердикт |
|---|---------|------|---------|
| 1 | `uv run ruff check ex_window_app_customtkinter/` | 0 | PASS — `All checks passed!` |
| 2 | `uv run python -m ex_window_app_customtkinter.main_window_app --smoke valid_bracket` | 0 | PASS — вывод содержит результат проверки скобок: `inn() - res = (True, '({[]})')` и `(False, '[', '(')` |
| 3 | `xvfb-run -a uv run python -m ex_window_app_customtkinter.main_window_app --smoke-window 3` | 0 | PASS — exit 0, stdout/stderr пусты (0 байт), нет warning'ов `wraplength`, нет `bad pad value`, нет `TclError`, нет traceback |
| 4 | `uv run python -c "from ex_window_app_customtkinter.application_window import ApplicationWindow; print('import ok')"` | 0 | PASS — `import ok` |

## Сверки

| # | Команда | Результат | Ожидание | Вердикт |
|---|---------|-----------|----------|---------|
| 1 | `grep -cE 'name="(padx|pady)">\(' ex_window_app_customtkinter/window_app.ui` | 0 | 0 | PASS |
| 2 | `grep -c wraplength ex_window_app_customtkinter/window_app.ui` | 0 | 0 | PASS |
| 3 | `grep -c _patch_layout_pad_values ex_window_app_customtkinter/application_window.py` | 0 | 0 | PASS |

Дополнительные sanity-проверки:
- `grep -cE '\([0-9]+, [0-9]+\)' ex_window_app_customtkinter/window_app.ui` = 0 —
  ни одного скобочного кортежа не осталось.
- `grep -cE 'name="(padx|pady)">[0-9]+' ex_window_app_customtkinter/window_app.ui` = 41 —
  одиночные значения padx/pady не задеты.
- Сырой вывод smoke-window (0 байт): см. `tasks/current/dev/phase05_raw.txt`.

## Сводка изменений

- `application_window.py`: 738 → 648 строк (-90 строк).
- `window_app.ui`: 461 → 455 строк (-6 строк: 5 wraplength + 1 лишний
  перевод строки).
- `main_window_app.py`: без правок (264 строки, переименование сделано
  в фазе 2).

## Вердикт

**Checkpoint фазы 5 — зелёный.** Все три целевые grep-сверки
вернули 0, ruff чист, smoke и smoke-window работают без warning'ов
и traceback'ов. Техдолг фазы 4 (`_patch_layout_pad_values`) ликвидирован.
