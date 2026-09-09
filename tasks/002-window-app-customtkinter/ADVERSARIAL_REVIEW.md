# Adversarial Review — задание customtkinter (2026-09-09)

Задание: GUI-пример `ex_window_app_customtkinter` на CustomTkinter + pygubu.
Атаковал CLI-крайности, поведение окна под Xvfb :99 (не наш — чужой, не трогал), и программные сценарии.
Все запуски с timeout 30–120 с, после прогонов процессов не оставляю.

Сводка: **1 критический блокирующий дефект** (запуск любого примера через GUI падает);
**3 средних** (ширина сайдбара, дефект `minsize()`, молчаливая защита от 0/отрицательных секунд);
**3 низких** (мелкие UX/дизайн-расхождения со спекой). Остальные 6+ атак выдержаны.

---

## ADV-001: CTkProgressBar.start() падает TypeError — запуск примера через GUI невозможен
- **Команда/сценарий:** программно `app._on_card_click("valid_bracket")` → `app._on_run_clicked()` (или эквивалент через клик по кнопке «Запустить»). Также воспроизводится через `application_window.py:750` в `_start_example`.
- **Ожидание:** прогресс-индикатор стартует (CustomTkinter docs декларируют `start()` без аргументов либо `start(interval_ms)` — как у tkinter.ttk.Progressbar). В коде используется `self.progressbar.start(_QUEUE_POLL_MS)` с шагом 100 мс.
- **Факт:** `TypeError: CTkProgressBar.start() takes 1 positional argument but 2 were given`. Проверено: в `customtkinter/windows/widgets/ctk_progressbar.py:252` метод `def start(self):` — сигнатура НЕ принимает никаких аргументов кроме self (в этой версии CTk `start` без параметров, `stop` тоже без параметров; период анимации встроен в реализацию `_internal_loop`). Полный traceback:
  ```
  File ".../application_window.py", line 706, in _on_run_clicked
      self._start_example(example_id)
  File ".../application_window.py", line 750, in _start_example
      self.progressbar.start(_QUEUE_POLL_MS)
  TypeError: CTkProgressBar.start() takes 1 positional argument but 2 were given
  ```
  Воспроизводится в любом из сценариев: одиночный клик «Запустить», двойной клик подряд, запуск после переключения свитча, запуск в окне под Xvfb. Сценарии `startup`, `select_card`, `search_no_match`, `copy_empty`, `clear`, `geometry` отработали (до падения на `_on_run_clicked`).
- **Серьёзность:** критично.
- **Disposition:** ACCEPTED -> DEF-001.

## ADV-002: Ширина sidebar_frame — 233 px вместо заявленных в спеке 280 px
- **Команда/сценарий:** под Xvfb :99 поднять `ApplicationWindow`, после `update_idletasks()` запросить `app.sidebar_frame.winfo_width()`.
- **Ожидание:** в дизайн-спецификации сказано: «**Сайдбар** (`CTkFrame` id `sidebar_frame`, ширина фиксированная 280 px)». В `.ui` на `sidebar_frame` стоит `<property name="width">280</property>`. Ожидаемая фактическая ширина sidebar_frame — 280 px.
- **Факт:** `app.sidebar_frame.winfo_width() == 233` на окне 900x600 (default geometry). `content_frame.winfo_width() == 619`. Итого: 233 + 619 + 2*12 (padx на main_frame) + 0 = 876, не 900; 24 px «потеряно» (вероятно, из-за того, что CTkFrame при `width=280` свойство использует как `requested_width` и без явного `pack_propagate(False)`/принудительной `grid_configure(width=...)` ширина считается по содержимому — padx=12+8 внутри scroll + бордюры = 233). При ресайзе до 800x520 — sidebar остаётся 233, content 519. При 1400x900 — sidebar всё ещё 233, content 1119.
- **Серьёзность:** средне (визуальное расхождение с дизайн-спецификацией).
- **Disposition:** ACCEPTED -> DEF-002 (объединён с ADV-007 — один корень).

## ADV-003: `app.window.minsize()` падает TypeError в CustomTkinter
- **Команда/сценарий:** `DISPLAY=:99 uv run python -c "from ex_window_app_customtkinter.application_window import ApplicationWindow; app=ApplicationWindow(); print(app.window.minsize())"`.
- **Ожидание:** CTk переопределяет `Tk.minsize`, чтобы корректно работать с тёмной темой; вызов без аргументов возвращает текущий minsize как кортеж. Это документированный API tkinter.
- **Факт:** `TypeError: '<' not supported between instances of 'int' and 'NoneType'` в `customtkinter/windows/ctk_tk.py:184` (`if self._current_width < width:`). То есть CTk-обёртка над `minsize()` не инициализирует `_current_width` и падает. Сам `ApplicationWindow` вызывает `self.window.minsize(*_WINDOW_MINSIZE)` в `__init__` — там args переданы, и падения нет. Но если в дальнейшем понадобится опросить minsize (например, в `WM_DELETE_WINDOW` или в test-helper), вызов упадёт. Это **внутренний баг CTk**, не продукта; фиксить в нашем коде — на усмотрение оркестратора.
- **Серьёзность:** низко (проявится только при попытке опросить minsize; в текущем использовании не вызывается).
- **Disposition:** REJECTED — внутренний дефект CustomTkinter 6.0.0 (`customtkinter/windows/ctk_tk.py:184`), не код продукта; наш код `minsize()` без аргументов не вызывает, чинить чужую библиотеку вне рамок задания.

## ADV-004: `--smoke-window -5` молча превращается в 1 мс, не сигналит об ошибке
- **Команда/сценарий:** `DISPLAY=:99 uv run python -m ex_window_app_customtkinter.main_window_app --smoke-window -5`.
- **Ожидание:** либо argparse режет (как в случае с `abc`/`""`), либо явная валидация `seconds >= 0` с понятным сообщением. Отрицательная задержка не имеет смысла.
- **Факт:** `main_window_app.py:178` — `delay_ms = max(1, int(round(seconds * 1000)))`. Для `-5` → `max(1, int(round(-5 * 1000)))` → `max(1, -5000)` → `1`. Окно поднимается и мгновенно закрывается; exit=0. Пользователь не получает ни предупреждения, ни кода ошибки. По симметрии `--smoke-window 0` ведёт себя так же (но 0 в данном контексте «пограничный» — допустимо ли молча выставлять 1 мс, решает оркестратор; для отрицательных значений однозначно стоит вернуть ошибку).
- **Серьёзность:** средне (UX/валидация CLI).
- **Disposition:** ACCEPTED -> DEF-003.

## ADV-005: `--smoke-window ""` — argparse падает с `invalid float value: ''`, а не использует default
- **Команда/сценарий:** `DISPLAY=:99 uv run python -m ex_window_app_customtkinter.main_window_app --smoke-window ""`.
- **Ожидание:** при пустой строке (как и при отсутствии значения после `--smoke-window`) поведение должно быть одинаковым — взять `_DEFAULT_SMOKE_WINDOW_SECONDS = 5.0`. Либо единообразно обрезать в default, либо единообразно падать.
- **Факт:** без значения — `const=5.0` подставляется, ок=0. С `--smoke-window ""` — `argparse` зовёт `float("")` → `argparse.ArgumentTypeError` → `error: argument --smoke-window: invalid float value: ''`, exit=2. Это асимметрия: `--smoke-window 5.0` ок, `--smoke-window ""` (что по сути «пустое значение после флага») — падает. По контракту `nargs="?"` пустая строка должна трактоваться как «значение не передано» (так делает `bash`/argparse по спеке); argparse здесь ведёт себя иначе.
- **Серьёзность:** низко (пограничный случай CLI, в реальной эксплуатации маловероятен).
- **Disposition:** REJECTED — стандартное поведение argparse при `type=float` и явном значении `""`: мусорный ввод отсеивается с понятной ошибкой и exit 2; унификация с `nargs="?"` default не требуется, «работает как задумано».

## ADV-006: Гонка `progressbar.start()` бросает исключение в UI-потоке без обработки — orphan worker и `disabled` UI
- **Команда/сценарий:** воспроизводится при ЛЮБОМ клике «Запустить» (см. ADV-001). После `TypeError` в `_start_example`:
  - `self._set_running(True)` уже НЕ вызван (падает ДО него), значит кнопка «Запустить» остаётся активной;
  - `self._worker` уже создан (`threading.Thread(target=...)` ниже) и стартовал — НЕТ, на самом деле `self._worker.start()` идёт ПОСЛЕ `self.progressbar.start(...)`, поэтому воркер тоже не создан;
  - `self._set_status(_STATUS_RUNNING)` не вызван;
  - НО `self._append_output(f"=== Запуск: {title} ({example_id}) ===\n")` уже выполнен до `progressbar.start()`, поэтому в `output_text` осталась строка-заголовок.
- **Ожидание:** либо явная обработка исключения (cleanup + откат `_append_output`), либо прогресс-индикатор должен принимать аргумент (как в tkinter.ttk.Progressbar). В коде `_start_example` после `progressbar.start(...)` идёт `_worker.start()` и `after(...)` — если `start` упал, эти строки не выполнены, но `output_text` уже не пустой и заголовок висит как «артефакт полузапуска».
- **Факт:** в `tasks/current/dev/adv_programmatic_test.py` шаги `run_valid_bracket`, `double_run`, `switch_clear_off` все завершились `TypeError` ДО `self._worker = ...`; в `output_text` осталась запись `=== Запуск: ... ===` от `_append_output` (до падения). UI остался в «прерванном» состоянии: вывод не очищен, статус «Готово», карточка выбрана, но прогресс «не начат». Пользователь должен нажать «Очистить» или ещё раз «Запустить» (повторная попытка тоже упадёт).
- **Серьёзность:** критично (следствие ADV-001, но отдельная UX-проблема — нет отката при ошибке старта).
- **Disposition:** ACCEPTED -> DEF-001 (объединён с ADV-001 — общий корень; фикс: корректный вызов start() + перенос заголовка вывода после успешного старта потока, чтобы исключение не оставляло артефакт).

## ADV-007: Ширина `sidebar_frame` НЕ фиксируется — `width=280` в .ui игнорируется
- **Команда/сценарий:** `app.sidebar_frame.winfo_width()` при разных размерах окна (см. ADV-002, тот же тест).
- **Ожидание:** «ширина фиксированная 280 px» — то есть sidebar не должен растягиваться/сжиматься при ресайзе окна. Реализация через `grid_configure(width=280)` в `__init__` или `pack_propagate(False)`.
- **Факт:** sidebar 233 px на всех размерах (900x600, 800x520, 1400x900). То есть он действительно «фиксирован» — но не на 280, а на 233 (свой собственный `requested_width` по содержимому). Grid-вес `columnconfigure(0, weight=0)` соблюдён, но целевая ширина не та, что в спеке. Возможные причины: CTkFrame при `width=280` в `<property>` использует это как `_desired_width`, но без явного `configure(width=280)` или `grid_propagate(False)` он сжимается до минимума по содержимому; padx=8 на `cards_scroll` (8+8=16) + padx=12 на entry + 1-px бордюры ≈ 30 px «уходит» из 280, остаётся ~250; CTkFrame при этом округляет до 233.
- **Серьёзность:** средне (то же, что ADV-002, другая грань).
- **Disposition:** ACCEPTED -> DEF-002 (объединён с ADV-002 — один корень).

---

## Не воспроизведённые атаки (приложение выдержало)

- `--smoke nonexistent_example` — exit 2, понятное сообщение `"Unknown example id: 'nonexistent_example'. Known ids: ..."`. ✓
- `--smoke` без аргумента — берёт первый пример из реестра (async_context_var), exit 0. ✓
- `--smoke` всех 5 примеров по имени (`async_context_var`, `valid_bracket`, `zip_operations`, `metaclass_vars`, `multiprocessing_demo`) — exit 0, вывод содержит ожидаемый текст (для multiprocessing — 0.2 с реального времени, логи Pool/Executor корректно пришли). ✓
- `--smoke-window 3` / `0.5` / `1e-9` — exit 0, окно поднимается и закрывается через `after(...)`. ✓
- `--smoke valid_bracket --smoke-window 3` одновременно — exit 2, понятное сообщение про взаимоисключающие флаги. ✓
- `--unknown-flag` — argparse падает `unrecognized arguments`, exit 2, usage на stderr. ✓
- `--help` — exit 0, usage и описания опций. ✓
- `.ui` под Builder — загружается без ошибок (`from pygubu import Builder; b = Builder(); b.add_from_file('ex_window_app_customtkinter/window_app.ui')` → exit 0). ✓
- Стартовое состояние окна: `output_text` пуст, `status='Готово'`, `metric_registry='5'`, `metric_status='Готово'`, `metric_last_run='—'`, `search_counter='Найдено: 5 из 5'`, `example_title='Выберите пример'`, `_selected_example_id=None`, 5 карточек. ✓
- `run_no_selection` (клик «Запустить» без выбора) — статус `'Сначала выберите пример'`, вывод не изменился, не падает. ✓
- Программный выбор карточки (`_on_card_click`) — `_selected_example_id` обновлён, `status='Выбран: ...'`, `example_title` показывает название. ✓
- Поиск: `qqq_no_match` → `Найдено: 0 из 5`, все 5 карточек `winfo_viewable() == False`. ✓
- Поиск `zip` → `Найдено: 1 из 5`. ✓
- Поиск unicode (`контекст`, `🔥`) и длинная строка (`'a'*5000`) — не падают, корректно 0/5. ✓
- `copy_empty` — статус `'Нечего копировать'`, буфер не тронут. ✓
- `copy` с непустым выводом — clipboard действительно содержит вставленный текст, статус `'Вывод скопирован'`. ✓
- `clear` на пустом/непустом выводе — не падает, статус `'Готово'`, выбранная карточка сохраняется. ✓
- Hover/click/leave на карточке: enter → `fg=#363e59` (hover), click → `fg=#2f334d, border=#7aa2f7` (selected), leave → остаётся selected-цвет. ✓
- `_set_cards_bind_enabled(False)` — bind'ы снимаются на время выполнения, повторный bind восстанавливается. ✓
- Ресайз окна до minsize (800x520) — sidebar 233, content 519, content не схлопывается в 1 px. ✓
- Ресайз ниже minsize (500x300) — clamping в 800x520 (Tk `wm_minsize` работает). ✓
- Ресайз 1400x900 — sidebar 233 (фикс.), content 1119, растягивается. ✓
- `output_text` с `state='disabled'` — `_append_output` принудительно ставит `normal`, не падает. ✓
- `_copy_output_to_clipboard` на disabled output — возвращает корректно. ✓
- `clear_before_run_switch` начальное состояние — `1` (включён). ✓
- `autoscroll_switch` начальное состояние — `1` (включён). ✓

---

## Процессы после прогона

- Своих процессов `main_window_app`/`adv_programmatic`/`uv run python` не оставлено (финальный `pgrep` — пусто).
- Xvfb :99 (pid 3416210) — чужой, **не наш**, не трогал.

## Файлы артефактов

- `tasks/current/screenshots/adv_window.png` — скриншот стартового окна под Xvfb 1024x768 (900x600 окно по центру).
- `tasks/current/dev/adv_programmatic_test.py` — программный тест (создан для прогона; не артефакт продукта).
