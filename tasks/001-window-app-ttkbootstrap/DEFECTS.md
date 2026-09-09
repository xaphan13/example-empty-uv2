# DEFECTS

## DEF-001: --smoke-window с нечисловым значением даёт traceback вместо ошибки аргумента
- Серьёзность: low (CLI-эргономика, функциональность не ломается)
- Источник: ADVERSARIAL_REVIEW.md ADV-001 (disposition: ACCEPTED -> DEF-001)
- Шаги воспроизведения:
  1. `uv run python -m ex_window_app_ttkbootstrap.main_window_app --smoke-window abc`
  2. `uv run python -m ex_window_app_ttkbootstrap.main_window_app --smoke-window 5x`
- Ожидаемое: чистое сообщение об ошибке аргумента
  (`argparse type=float: "argument --smoke-window: invalid float value: 'abc'"`),
  exit=2
- Фактическое: необработанный `ValueError` с полным traceback на stderr, exit=1
- Статус: CLOSED
- History:
  - 2026-09-08 — заведён qa по результату adversarial-прогона (ADV-001).
    Воспроизведено пачкой: оба кейса (`abc`, `5x`) дают
    `ValueError: could not convert string to float: '<input>'` из
    `ex_window_app_ttkbootstrap/main_window_app.py:240` (`return _run_smoke_window(float(seconds))`),
    traceback через `main` → `raise SystemExit(main())` на строке 251, exit=1.
    Сырой вывод: `tasks/current/e2e/qa_adv001_repro.txt`.
  - 2026-09-08 — ИСПРАВЛЕНО backend-dev: к аргументу `--smoke-window`
    добавлен `type=float` (валидация на этапе argparse, чистое сообщение
    `invalid float value`, exit=2); убраны мёртвая ветка
    `if seconds is False` и приведение `float(seconds)` в `main()`.
    Checkpoint: ruff чист; `abc`/`5x` → exit=2 без traceback;
    `2`/`0.001`/`-1` под Xvfb → exit=0; `--smoke valid_bracket` → exit=0;
    оба флага сразу → exit=2. Подробности:
    `tasks/current/dev/phase04_progress.md`, секция «Фикс DEF-001».
  - 2026-09-08 — qa перепроверил фикс: все кейсы сходятся (`abc`/`5x` → exit=2 без traceback, ruff чист, smoke работает, взаимоисключение работает, smoke-window под Xvfb exit=0). Сырой вывод: e2e/qa_def001_recheck.txt. Статус: CLOSED.

### Ключевые строки traceback (из воспроизведения)

```
  File "/home/max/0_0_26_new_one/example-empty-uv2/ex_window_app_ttkbootstrap/main_window_app.py", line 240, in main
    return _run_smoke_window(float(seconds))
                             ^^^^^^^^^^^^^^
ValueError: could not convert string to float: 'abc'
exit=1
```

```
  File "/home/max/0_0_26_new_one/example-empty-uv2/ex_window_app_ttkbootstrap/main_window_app.py", line 240, in main
    return _run_smoke_window(float(seconds))
                             ^^^^^^^^^^^^^^
ValueError: could not convert string to float: '5x'
exit=1
```
