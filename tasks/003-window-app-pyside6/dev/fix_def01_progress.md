# Прогресс — исправление DEF-001/002/003 (main_window_app.py)

- 2026-09-11 — воспроизведены все три дефекта до правки:
  `--smoke-window inf` → `OverflowError: cannot convert float infinity to integer`, exit=1;
  `--smoke-window nan` → `ValueError: cannot convert float NaN to integer`, exit=1;
  `--smoke-window 1e309` → `OverflowError: cannot convert float infinity to integer`, exit=1.
  Все — строка 111 `main_window_ctk.py`, `int(args.smoke_window * 1000)`.
- 2026-09-11 — правка `_positive_float`: добавлен `import math`, условие
  `if not math.isfinite(seconds) or seconds <= 0:`. Статус: применено.
- 2026-09-11 — checkpoint зелёный (сырой вывод — `tasks/current/dev/fix_def01_checkpoint.txt`):
  ruff exit=0; `inf`, `nan`, `1e309`, `-1`, `abc` → exit=2, сообщение в stderr, без traceback;
  `--smoke` → `smoke ok`, exit=0; `--smoke-window 3` → exit=0, elapsed=3s.