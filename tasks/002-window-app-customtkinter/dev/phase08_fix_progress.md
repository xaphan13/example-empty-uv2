# Phase 08 — fix DEF-001 / DEF-002 / DEF-003

Дата: 2026-09-09.
Исправительный прогон backend-dev по итогам триажа DEFECTS.md.

## Зона
- ex_window_app_customtkinter/application_window.py (DEF-001, DEF-002)
- ex_window_app_customtkinter/main_window_app.py (DEF-003)
- tasks/current/dev/* — артефакты этого прогона

## Правки

### DEF-001 — application_window.py, метод `_start_example`
- `self.progressbar.start(_QUEUE_POLL_MS)` → `self.progressbar.start()`
  (CTk 6.0.0: `CTkProgressBar.start()` не принимает аргументов; в
  библиотеке период анимации встроен).
- Заголовок `self._append_output(f"=== Запуск: {title} ({example_id}) ===\n")`
  перенесён ПОСЛЕ `self._worker.start()` (и `after(...)`), чтобы
  исключение при старте потока не оставляло «голый» заголовок
  в output_text (артефакт полузапуска из ADV-006).
- Создание/старт воркера обёрнуты в `try/except`: при исключении
  откатываем UI (`progressbar.stop()`, `_set_running(False)`,
  статус «Ошибка») и пробрасываем. Это закрывает гонку из ADV-006
  минимальной защитой.

### DEF-002 — application_window.py, `main_frame.columnconfigure`
- `self.main_frame.columnconfigure(0, weight=0, minsize=304)` —
  minsize=280 (как в спеке) компенсирует `padx=12` в
  `sidebar.grid_configure(...)`: Tk-grid отдаёт sidebar'у
  `cell - 2*padx` (280+12+12=304 → 280 px видимой ширины).
  Без явного minsize sidebar сжимался по содержимому до ~233 px.
  Параметры колонки 1 (weight=1) не тронуты.

### DEF-003 — main_window_app.py
- Добавлена type-функция `_positive_float(raw)`: парсит float,
  требует строго > 0, иначе `argparse.ArgumentTypeError` с
  понятным текстом "значение должно быть числом > 0 (получено ...)".
- `--smoke-window` подключён к `type=_positive_float` вместо
  `type=float`. Мусор (`-5`, `0`) → exit=2 с сообщением argparse.
  Семантика `nargs="?"`, `const`, взаимоисключающих флагов и
  `--smoke` не тронута.

## Checkpoint
- `uv run ruff check ex_window_app_customtkinter/` → All checks passed.
- `DISPLAY=:99 uv run python -m ex_window_app_customtkinter.main_window_app --smoke-window 5` → exit=0, без traceback.
- `uv run python -m ex_window_app_customtkinter.main_window_app --smoke valid_bracket` → exit=0, ожидаемый вывод.
- `uv run python -m ex_window_app_customtkinter.main_window_app --smoke-window -5` → exit=2, "значение должно быть числом > 0 (получено '-5')".
- `uv run python -m ex_window_app_customtkinter.main_window_app --smoke-window 0` → exit=2, "значение должно быть числом > 0 (получено '0')".

## Функциональная проверка DEF-001 (под Xvfb :99)
Скрипт `phase08_def001_check.py`: выбрать valid_bracket, кликнуть
«Запустить», дождаться завершения, опросить виджеты.
- `step1_ok: True` — запуск БЕЗ TypeError.
- `output_len: 419` — вывод дошёл (заголовок + логи).
- `has_launch_header: True`, `has_result: True` — структура ответа корректна.
- `status: 'Завершено'`, `metric_status: 'Завершено'` — терминальный статус.
- `sidebar_w: 280` — DEF-002 закрыт.
- `worker_alive: False` — воркер завершился штатно.

## Артефакты
- `phase08_checkpoint.txt` — сырой вывод 4 checkpoint-команд.
- `phase08_def001_raw.txt` — сырой вывод функциональной проверки.
- `phase08_def001_check.py` — тестовый скрипт.
