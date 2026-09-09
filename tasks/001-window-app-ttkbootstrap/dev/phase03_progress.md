# Фаза 3: Оконный класс — прогресс

Дата: 2026-09-08
Сессия: backend-dev
Задание: `ex_window_app_ttkbootstrap/application_window.py` — класс `ApplicationWindow`
с wiring виджетов, фильтрацией, сменой тёмной темы, запуском примеров
в `threading.Thread` и доставкой вывода через `queue.Queue` + `window.after`.

## План (выполнен)

1. Создать прогресс-файл.
2. Одним `write_file` создать `application_window.py`:
   - `__init__` — загрузка `.ui` от `Path(__file__).with_name(...)`, привязка
     виджетов по id, наполнение combobox'ов, подключение обработчиков.
   - Приватные методы: фильтрация, смена темы, запуск в потоке, опрос
     очереди из главного потока, безопасная очистка/запись `output_text`.
3. Прогнать checkpoint из спецификации: ruff, `Builder().add_from_file`,
   импорт класса (без дисплея).
4. Опционально под `xvfb-run` — инстанцировать окно и проверить
   happy/error paths через воркер.

## Структура класса

- `__init__`:
  - `ui_path = Path(__file__).with_name("window_app.ui")` — не от cwd.
  - `self.window = ttkbootstrap.Window(title=..., themename="darkly")`.
  - `pygubu.Builder` + `add_from_file` + `get_object("main_frame", ...)`.
  - Привязка виджетов по 8 обязательным id из фазы 2 (через
    `builder.get_object`); плюс `output_scroll` (опционально,
    связывается с `output_text.yview`).
  - Маппинг `title ↔ example_id` через `list_examples()`; в combobox
    показываем title, запускаем по id.
  - `theme_combobox.values = ("darkly", "superhero", "cyborg", "solar", "vapor")`,
    стартовое `darkly`.
  - `progressbar.stop()` на старте (страховка от визуального «застрявания»).
  - Подключение обработчиков: `<<ComboboxSelected>>` для темы,
    `StringVar.trace_add("write", ...)` для фильтра, `command=` для кнопок,
    `WM_DELETE_WINDOW` для закрытия.
- Приватные методы:
  - `_set_status(text)`, `_set_running(bool)` (блокировка UI),
    `_append_output(text)`, `_clear_output()` — все только из главного потока.
  - `_on_filter_changed` — фильтрация по подстроке (case-insensitive);
    сохраняет текущий выбор, если он остался в новом списке.
  - `_on_theme_selected` — `ttkbootstrap.Style().theme_use(...)`.
  - `_selected_example_id()` — `title → id` через `_title_to_id`.
  - `_on_run_clicked`, `_start_example` — подготовка UI + `Thread(daemon=True)`.
  - `_run_in_worker` — `run_example` под `try/except`; в очередь кладётся
    `("done", text)` или `("error", traceback)`.
  - `_poll_queue` — забирает `get_nowait`; на терминальном сообщении
    останавливает progressbar, разблокирует UI, выставляет «Завершено»/
    «Ошибка»; самопланируется через `window.after(_QUEUE_POLL_MS, ...)`,
    пока воркер жив или очередь не пуста.
  - `_on_clear_clicked`, `_on_close`.

## Сделанные правки

- `ex_window_app_ttkbootstrap/application_window.py` — новый файл,
  одним `write_file`.
- Точечная правка: в защитной ветке `_poll_queue` (воркер мёртв,
  очередь пуста, терминала не было) убрал `_set_status(_STATUS_READY)`,
  чтобы не перетирать «Ошибка»/«Завершено», выставленные терминальной
  веткой. Оставил только `progressbar.stop()` и `_set_running(False)`.
  В реальном `mainloop` этот путь не достигается, но в headless-симуляции
  (ручной `_poll_queue` без `after`) он срабатывал и затирал статус.

## Checkpoint

### ruff
```
$ uv run ruff check ex_window_app_ttkbootstrap/
All checks passed!
exit=0
```
Файл: `tasks/current/dev/phase03_ruff.txt`.

### pygubu Builder загружает .ui
```
$ uv run python -c "from pygubu import Builder; b = Builder(); b.add_from_file('ex_window_app_ttkbootstrap/window_app.ui'); print('ui loaded')"
ui loaded
exit=0
```
Файл: `tasks/current/dev/phase03_builder.txt`.

### Импорт класса headless (без дисплея)
```
$ uv run python -c "from ex_window_app_ttkbootstrap.application_window import ApplicationWindow; print('import ok')"
import ok
exit=0
```
Импорт не поднимает `Tk()`/`Window()` — `Window()` создаётся только
внутри `__init__`. Файл: `tasks/current/dev/phase03_import.txt`.

## Дополнительные проверки под Xvfb (не обязательные по спеке, но проведены)

### Smoke инстанцирования окна
```
$ xvfb-run -a uv run python -c "from ex_window_app_ttkbootstrap.application_window import ApplicationWindow; w = ApplicationWindow(); ..."
instance ok
window type: App
main_frame type: Frame
example combobox values head: ('Async: ContextVar в задачах', 'Code War: проверка скобочных последовательностей')
theme combobox values: ('darkly', 'superhero', 'cyborg', 'solar', 'vapor')
theme default: darkly
status: Готово
progressbar mode: indeterminate
filter=zip -> ['ZIP: запись и чтение архивов']
filter cleared -> ['Async: ContextVar в задачах', 'Code War: проверка скобочных последовательностей']
theme changed to cyborg -> style theme_use works
output after append: 'hello\nworld\n'
destroyed
```
- `Window` создан, `main_frame` упакован, 5 тем в `theme_combobox`,
  5 примеров в `example_combobox`, фильтр сокращает список до одного,
  смена темы не падает, `_clear_output`+`_append_output` работают.
Файл: `tasks/current/dev/phase03_xvfb_smoke.txt`.

### Happy path: воркер запускает valid_bracket
```
status: Завершено
output first 5 lines:
  === Запуск: Code War: проверка скобочных последовательностей (valid_bracket) ===
  2026-09-08 23:33:38 [INFO] OnlyFile: '****' main_code_war - 'start'
  2026-09-08 23:33:38 [INFO] OnlyFile: '****' run_valid - 'start'
  2026-09-08 23:33:38 [INFO] OnlyFile: inn() - res = (True, '({[]})')
  2026-09-08 23:33:38 [INFO] OnlyFile: inn() - res = (True, '({[]})')
```
- Воркер завершился, `_poll_queue` подхватил `("done", text)`,
  `progressbar.stop()`, `_set_running(False)`, статус «Завершено».
Файл: `tasks/current/dev/phase03_xvfb_run.txt`.

### Error path: воркер падает (run_example подменён на boom)
```
text status: Ошибка
text output head: === Запуск: Code War: ... ===\n[ОШИБКА]\nTraceback (most recent call la
button state: normal
combobox state: readonly
theme combobox state: readonly
filter state: normal
```
- Исключение из примера поймано в `_run_in_worker`, `traceback.format_exc()`
  положен в очередь, `_poll_queue` добавил `[ОШИБКА]\n...` в `output_text`,
  выставил «Ошибка», разблокировал UI.
Файл: `tasks/current/dev/phase03_xvfb_error.txt`.

## Замечания по контракту

- `output_text` обновляется только из `_poll_queue`, который запускается
  из `self.window.after(...)` — это всегда главный поток Tk. Воркер
  только кладёт данные в очередь. Дополнительной синхронизации
  не требуется.
- `run_example` пробрасывает исключения → воркер оборачивает
  `try/except Exception`, кладёт `("error", traceback.format_exc())` в очередь.
  Окно не падает, traceback виден в `output_text`.
- Пока `self._worker is not None`, повторный клик по `run_button` игнорируется;
  `_set_running(True)` дополнительно делает `state="disabled"` у кнопки
  и combobox'ов — защита от гонки.
- `KeyError` от `get_example`/`run_example` для неизвестного id теоретически
  невозможен (id берётся из реестра), но `KeyError` в очереди через
  `try/except Exception` всё равно поймается как обычный error-path.
- Стартовая тема — `darkly`; список тем фиксирован в `_DARK_THEMES`
  и не зависит от того, что есть в установленной версии ttkbootstrap.
- Импорт модуля не создаёт `Tk()`/`Window()`: только `import pygubu`,
  `import ttkbootstrap`, `from ... import list_examples, run_example`
  — всё без побочных GUI-эффектов. Подтверждено отдельным прогоном
  импорта в headless.

## Итог
Статус фазы: **ЗЕЛЁНЫЙ**.
- Файл `ex_window_app_ttkbootstrap/application_window.py` создан.
- Импорт класса работает headless (без дисплея).
- pygubu Builder загружает `window_app.ui` без ошибок.
- ruff чист по всему пакету.
- Под Xvfb: окно инстанцируется, фильтр/смена темы работают, happy
  path и error path через воркер отрабатывают корректно, UI
  разблокируется, статус «Завершено»/«Ошибка» выставляется верно.
- Никакие другие файлы не тронуты. Git не коммитился.
