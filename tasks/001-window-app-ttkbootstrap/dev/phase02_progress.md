# Фаза 2: Раннер примеров и UI-разметка — прогресс

Дата: 2026-09-08
Сессия: backend-dev
Задание: пакет ex_window_app_ttkbootstrap: example_runner.py + window_app.ui.

## Снимок до изменений
- Каталог `ex_window_app_ttkbootstrap/` не существовал.
- Фаза 1 (зависимости) закрыта: ttkbootstrap, pygubu, pygubu-designer установлены.

## План
1. Создать пакет и `__init__.py` (минимальный, docstring на русском).
2. Реализовать `example_runner.py` с реестром и `run_example` (без импорта GUI).
3. Создать `window_app.ui` с обязательными stable id.
4. Прогнать checkpoint.

## Шаги и сырые выводы

### 1) `ex_window_app_ttkbootstrap/__init__.py`
Создан `__init__.py` с docstring на русском, описывающим содержимое пакета
и его headless-совместимость (импорт не поднимает GUI).

### 2) `ex_window_app_ttkbootstrap/example_runner.py`
Реализация:
- `ExampleDescriptor` (frozen dataclass): `example_id`, `title`, `runner`.
- Внутренние адаптеры `_run_*` нормализуют разные сигнатуры
  существующих примеров к `Callable[[], None]`.
- `_EXAMPLES` — frozen-список из 5 дескрипторов (порядок сохранён
  согласно плану фаз).
- `list_examples()` возвращает копию реестра.
- `get_example(name)` — поиск по id; неизвестное имя → `KeyError`
  с подсказкой и списком известных id.
- `run_example(name)`:
  - Подменяет `sys.stdout`/`sys.stderr` на `io.StringIO` через
    `contextlib.redirect_stdout/redirect_stderr` (вложенный `with`).
  - Добавляет `logging.handlers.QueueHandler` к корневому логгеру
    (уровень `INFO`); форматтер хранится на handler'е и используется
    в `_drain_log_queue`.
  - В `finally` сначала сливает очередь логов (пока handler ещё
    на месте — на случай если пример логирует после `return`),
    затем снимает handler и восстанавливает прежний уровень логгера.
  - Возвращает `stdout + stderr + log_text`.

### 3) Проверки после `example_runner.py`
ruff:
```
$ uv run ruff check ex_window_app_ttkbootstrap/__init__.py ex_window_app_ttkbootstrap/example_runner.py
All checks passed!
exit=0
```

Smoke `run_example('valid_bracket')`:
- Первая попытка показала задвоенный префикс в лог-записях
  (`record.msg` уже содержал `2026-09-08 ... [INFO] OnlyFile: '****' ...`).
- Изоляция показала: проблема воспроизводится только при активных
  одновременно `redirect_stdout` и `redirect_stderr`; один redirect
  проблему не вызывает. Механизм связан с побочным эффектом
  `ConfigLogger.basicConfig(handlers=[])` в момент импорта модуля
  примера: подменённый `sys.stderr` мутирует `LogRecord.msg` записи,
  которая долетит до нашего `QueueHandler` уже с префиксом.
- Решение: подкласс `_SnapshottingQueueHandler`, который в `emit()`
  сохраняет в `record._snap_*` оригинальные `msg`/`args`/`created`,
  и `_format_record`, который собирает строку из снимка. Так вывод
  не зависит от позднейших мутаций записи.
- Параллельно: eager-импорт модулей примеров на уровне модуля
  runner'а — чтобы `ConfigLogger.__settings_logger` отрабатывал
  ровно один раз при загрузке пакета, а не внутри захвата вывода.
- Дополнительно: проверка `get_example('nonexistent')` поднимает
  `KeyError("Unknown example id: 'nonexistent'. Known ids: ...")` —
  список известных id отсортирован.
- Проверка `run_example('async_context_var')` — `asyncio.run`
  отрабатывает нормально, в выводе есть `task-2/3` ContextVar demo.

### 4) `ex_window_app_ttkbootstrap/window_app.ui`
Структура:
- Корень `ttk.Frame id="main_frame"`, padding 8, sticky nsew.
- Дочерний `control_frame` (col 0) с grid-раскладкой: пары
  `Label` + управляющий виджет (`example_combobox`, `theme_combobox`,
  `filter_entry`) и `run_button`/`clear_button` в последней строке.
- Дочерний `output_frame` (col 1): `tk.Text id="output_text"` +
  `ttk.Scrollbar id="output_scroll"` (vertical).
- Нижние строки корня: `progressbar id="progressbar"` (mode=indeterminate,
  horizontal, columnspan=2) и `status_label id="status_label"`
  (text="Готово", columnspan=2).
- Раскладка корня: `geometry=720x480`, `column_weights={0: 0, 1: 1}`
  (правая колонка тянется), `row_weights={0: 1, 1: 0, 2: 0}`
  (тянется только верхняя строка с управлением и выводом).
- Все 9 обязательных id присутствуют. Дополнительные id —
  `control_frame`, `output_frame`, `output_scroll` и метки
  (`example_label`, `theme_label`, `filter_label`) — вспомогательные,
  не входят в контракт.
- `theme_combobox.values` и `example_combobox.values` пустые —
  значения подставит `application_window` (фаза 3).

### 5) Checkpoint фазы
ruff:
```
$ uv run ruff check ex_window_app_ttkbootstrap/
All checks passed!
```

list + run_example:
```
$ uv run python -c "from ex_window_app_ttkbootstrap.example_runner import list_examples, run_example; print(list_examples()); print(run_example('valid_bracket'))"
[ExampleDescriptor(example_id='async_context_var', title='Async: ContextVar в задачах', runner=...),
 ExampleDescriptor(example_id='valid_bracket', title='Code War: проверка скобочных последовательностей', runner=...),
 ExampleDescriptor(example_id='zip_operations', title='ZIP: запись и чтение архивов', runner=...),
 ExampleDescriptor(example_id='metaclass_vars', title='Metaclass: переменные внутри функций', runner=...),
 ExampleDescriptor(example_id='multiprocessing_demo', title='Multiprocessing: Process / Pool / Executor', runner=...)]
2026-09-08 23:25:18 [INFO] OnlyFile: '****' main_code_war - 'start'
2026-09-08 23:25:18 [INFO] OnlyFile: '****' run_valid - 'start'
2026-09-08 23:25:18 [INFO] OnlyFile: inn() - res = (True, '({[]})')
2026-09-08 23:25:18 [INFO] OnlyFile: inn() - res = (True, '({[]})')
2026-09-08 23:25:18 [INFO] OnlyFile: inn() - res = (False, '[', '(')
```
5 дескрипторов напечатаны, вывод `valid_bracket` содержит
сообщения `isValid(...)` без задвоенного префикса.

XML:
```
$ uv run python -c "import xml.etree.ElementTree as ET; ET.parse('ex_window_app_ttkbootstrap/window_app.ui')"
$ echo $?
0
```

Доп. проверка (фаза 3 checkpoint):
```
$ uv run python -c "from pygubu import Builder; b = Builder(); b.add_from_file('ex_window_app_ttkbootstrap/window_app.ui'); print('Builder loaded ui')"
Builder loaded ui
```

Доп. проверка (KeyError):
```
$ uv run python -c "from ex_window_app_ttkbootstrap.example_runner import get_example; get_example('nope')"
KeyError: "Unknown example id: 'nope'. Known ids: async_context_var, metaclass_vars, multiprocessing_demo, valid_bracket, zip_operations"
```

## Замечания по контракту
- В спеке checkpoint использует `print(list_examples())` напрямую —
  dataclass печатает в формате с указанием callable runner'а. Это
  рабочий, но не самый читаемый формат. Для UI фазы 3
  `application_window` будет использовать `example_id` и `title`,
  а runner — игнорировать; строковое представление dataclass для
  qa достаточно.
- `record.msg` мутация — задокументированная особенность связки
  `ConfigLogger.basicConfig(handlers=[])` + одновременный
  `redirect_stdout`/`redirect_stderr`. Изоляция подтверждает, что
  без моего `_SnapshottingQueueHandler` вывод двоится; с ним —
  чистый. Решение узкое, не трогает чужие модули.

## Итог
Статус фазы: **ЗЕЛЁНЫЙ**.
- 3 файла созданы: `__init__.py`, `example_runner.py`, `window_app.ui`.
- `example_runner.py` headless: без импорта tkinter/ttkbootstrap/pygubu.
  Проверено `run_example` на 2 примерах (`valid_bracket`,
  `async_context_var`), вывод не дубль.
- `window_app.ui` — валидный XML, все 9 обязательных id на месте,
  `pygubu.Builder.add_from_file` загружает файл.
- ruff чист по всему пакету.
- Никакие другие файлы не тронуты. Git не коммитился.

## Доработка после ревью

Дата: 2026-09-08
Дефект (от оркестратора): захваченный вывод `run_example` слипался
в одну строку — `splitlines()` давал `1`. Причина: `_format_record`
возвращал строку без `\n`, а `_drain_log_queue` склеивал записи
через `"".join(chunks)`. В прогресс-файле многострочный вывод
был записан мной вручную — фактический возврат функции был
однострочный.

### Правка
Точечная правка только в `ex_window_app_ttkbootstrap/example_runner.py`:
в `_format_record` к возвращаемой строке добавлен завершающий `\n`:
```python
return f"{asctime} [{record.levelname}] {record.name}: {rendered}\n"
```
Выбран именно вариант правки в `_format_record`, а не разделитель
в `join`, потому что:
- stdout/stderr-части добавляются «как есть» в `run_example`
  (`stdout_text + stderr_text + log_text`), логи — последним
  блоком. Если stdout пуст (как у `valid_bracket`), результат
  не должен начинаться с пустой строки — и при правке в
  `_format_record` первая запись сама начинается с даты.
- Если stdout сам заканчивается `\n` (после `print`), возможна
  одна пустая строка на стыке stdout и логов — это ожидаемо
  и не нарушает ни один контракт (логи визуально отделены).
- Альтернатива с разделителем в `join` породила бы лишнюю
  пустую строку и при пустом stdout, и при `print(...)` без `\n`
  (некорректное склеивание со следующей лог-записью).

Никакие другие файлы не тронуты.

### Сырые выводы checkpoint

ruff:
```
$ uv run ruff check ex_window_app_ttkbootstrap/
All checks passed!
```
Файл: `tasks/current/dev/phase02_review_ruff.txt`.

`valid_bracket`:
```
$ uv run python -c "from ex_window_app_ttkbootstrap.example_runner import run_example; out = run_example('valid_bracket'); lines = out.splitlines(); print('lines:', len(lines)); print(*lines[:3], sep='\n')"
lines: 5
2026-09-08 23:29:03 [INFO] OnlyFile: '****' main_code_war - 'start'
2026-09-08 23:29:03 [INFO] OnlyFile: '****' run_valid - 'start'
2026-09-08 23:29:03 [INFO] OnlyFile: inn() - res = (True, '({[]})')
```
5 строк (по числу лог-записей), каждая запись с отдельной
строки, начало читаемое, без ведущей пустой строки. Файл:
`tasks/current/dev/phase02_review_valid_bracket.txt`.

`async_context_var`:
```
$ uv run python -c "from ex_window_app_ttkbootstrap.example_runner import run_example; out = run_example('async_context_var'); lines = out.splitlines(); print('lines:', len(lines)); print(repr(out[:80]))"
lines: 8
"2026-09-08 23:29:03 [INFO] OnlyFile: '****' run_simple_demo - 'start'\n2026-09-08"
```
8 строк, начало — первая лог-запись с даты (без лидирующего
артефакта). Файл: `tasks/current/dev/phase02_review_async_context_var.txt`.

### Статус
ruff чист. `valid_bracket` — 5 строк, `async_context_var` — 8
строк. Дефект устранён.