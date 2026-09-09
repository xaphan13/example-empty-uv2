# DEFECTS.md — задание «Перевод GUI-примера с ttkbootstrap на CustomTkinter»

Заведены оркестратором по итогам триажа ADVERSARIAL_REVIEW.md (2026-09-09).
ADV-001 + ADV-006 → DEF-001 (общий корень); ADV-002 + ADV-007 → DEF-002 (общий корень);
ADV-004 → DEF-003; ADV-003, ADV-005 — REJECTED (см. disposition в ADVERSARIAL_REVIEW.md).

---

## DEF-001: Запуск примера через GUI падает — CTkProgressBar.start() не принимает аргумент

- Серьёзность: критическая.
- Источник: ADV-001, ADV-006.
- Статус: CLOSED.
- Воспроизведение: запустить окно (`python -m ex_window_app_customtkinter.main_window_app`), выбрать карточку, нажать «Запустить». Traceback: `TypeError: CTkProgressBar.start() takes 1 positional argument but 2 were given` (`application_window.py`, `_start_example`, вызов `self.progressbar.start(_QUEUE_POLL_MS)`). В CustomTkinter 6.0.0 `start()` без аргументов (см. `customtkinter/windows/widgets/ctk_progressbar.py`).
- Ожидание: клик «Запустить» запускает пример в потоке, прогресс анимируется, вывод приходит в output_text, статус «Завершено».
- Факт: TypeError в UI-потоке; пример не запускается; в output_text остаётся артефакт `=== Запуск: ... ===` (заголовок дописывается до падения), откатa нет. Главный пользовательский сценарий сломан; headless `--smoke` не затронут.
- Требование к фиксу: `self.progressbar.start()` без аргумента; `_append_output` заголовка перенести после успешного старта воркера (или защитить блок `_start_example` try/except с откатом состояния), чтобы исключение не оставляло полузапуск.
- History:
  - 2026-09-09 — заведён оркестратором (триаж adversary).
  - 2026-09-09 — backend-dev: ИСПРАВЛЕНО. «`self.progressbar.start()` без аргумента; заголовок `=== Запуск:` перенесён после успешного старта воркера; создание/старт воркера обёрнут в try/except с откатом (progressbar.stop(), _set_running(False), статус „Ошибка“)». Функциональная проверка под Xvfb: без TypeError, output_len 419, has_result True, статус «Завершено». Статус FIX-READY.
  - 2026-09-09 — qa: перепроверен независимо под Xvfb. Сценарий `app._on_card_click("valid_bracket")` → `app._on_run_clicked()` → `after(4000, verify)`. Результат: `step1_ok=True`, `output_len=419`, `has_launch_header=True`, `has_result=True`, `status='Завершено'`, `metric_status='Завершено'`, `worker_alive=False`, никакого TypeError/traceback. Регресс вокруг: `--smoke valid_bracket` → exit 0; `--smoke-window 3` → exit 0; ruff чист. Фикс подтверждён. Статус CLOSED. Доказательство: `tasks/current/e2e/05_defects.txt` (BATCH 1, BATCH 2).

## DEF-002: Фактическая ширина сайдбара 233 px вместо 280 px из дизайн-спецификации

- Серьёзность: средняя.
- Источник: ADV-002, ADV-007.
- Статус: CLOSED.
- Воспроизведение: поднять `ApplicationWindow`, вызвать `update_idletasks()`, запросить `app.sidebar_frame.winfo_width()` → 233 при любом размере окна (900x600, 800x520, 1400x900).
- Ожидание: дизайн-спецификация v2 — «ширина фиксированная 280 px»; `width=280` в `.ui` является requested_width и сжимается по содержимому, т.к. grid-менеджер не удерживает requested size без minsize/propagate-off.
- Факт: сайдбар стабильно 233 px; расхождение с зафиксированной спекой.
- Требование к фиксу: `self.main_frame.columnconfigure(0, minsize=280)` (или эквивалент, удерживающий 280 px) при сохранении растяжения content-колонки.
- History:
  - 2026-09-09 — заведён оркестратором (триаж adversary).
  - 2026-09-09 — backend-dev: ИСПРАВЛЕНО. «`columnconfigure(0, weight=0, minsize=304)`: при существующих `padx=12` в grid_configure сайдбара Tk отводит ячейке 304, виджет получает 304-24=280 видимых px; буквальный minsize=280 давал бы 256 видимых. Проверено: sidebar_w 280 на 900x600 и 1400x900, контент растягивается». Решение оркестратора: эквивалент принят (контракт дефекта — видимая ширина 280). Статус FIX-READY.
  - 2026-09-09 — qa: перепроверен независимо. Сценарий: поднять `ApplicationWindow`, опросить `sidebar_frame.winfo_width()` на дефолтном окне, на 1400x900 и на 800x520. Результат: `sidebar_w=280` (дефолт), `big_sidebar_w=280` (1400x900), `min_sidebar_w=280` (800x520). Контент растягивается: `content_w=572` (дефолт), `big_content_w=1072` (1400x900), `min_content_w=472` (800x520) — 1072 > 472, контракт дизайн-спецификации выполнен. Фикс подтверждён на всех трёх размерах. Статус CLOSED. Доказательство: `tasks/current/e2e/05_defects.txt` (BATCH 2, BATCH 3).

## DEF-003: `--smoke-window -5` молча превращается в задержку 1 мс

- Серьёзность: средняя.
- Источник: ADV-004.
- Статус: CLOSED.
- Воспроизведение: `uv run python -m ex_window_app_customtkinter.main_window_app --smoke-window -5` — окно поднимается и мгновенно закрывается, exit 0, без предупреждения (`main_window_app.py`: `delay_ms = max(1, int(round(seconds * 1000)))`).
- Ожидание: отрицательное (и нулевое) значение секунд — мусорный ввод: argparse должен отклонить его с понятным сообщением и exit 2, аналогично невалидному float.
- Факт: ввод принимается молча, задержка clamp'ится к 1 мс; пользователь не узнаёт об ошибке.
- Требование к фиксу: type-функция для `--smoke-window`, принимающая только строго положительные числа (сообщение вида «seconds must be > 0»); `max(1, ...)` после этого не нужен, но вреда не несёт.
- History:
  - 2026-09-09 — заведён оркестратором (триаж adversary).
  - 2026-09-09 — backend-dev: ИСПРАВЛЕНО. «Добавлена type-функция `_positive_float` (float + требование > 0, иначе `argparse.ArgumentTypeError`); `--smoke-window` теперь `type=_positive_float`; nargs/const/default и семантика остальных флагов не менялись. Проверено: `-5` и `0` → exit 2 с сообщением `значение должно быть числом > 0 (получено '-5'/'0')`; `--smoke-window 5` → exit 0». Статус FIX-READY.
  - 2026-09-09 — qa: перепроверен независимо. `--smoke-window -5` → exit 2, `argument --smoke-window: значение должно быть числом > 0 (получено '-5')`. `--smoke-window 0` → exit 2, сообщение с `'0'`. `--smoke-window abc` → exit 2, `invalid float value: 'abc'` (стандартный argparse, как и было). `--smoke-window ""` → exit 2, `invalid float value: ''`. `--smoke-window 3` (под Xvfb) → exit 0, окно поднимается и закрывается. `--smoke valid_bracket` → exit 0, вывод скобок присутствует. Ruff `ex_window_app_customtkinter/` → All checks passed. Фикс полностью закрывает сценарий ADV-004, нерегрессии нет. Статус CLOSED. Доказательство: `tasks/current/e2e/05_defects.txt` (BATCH 1).
