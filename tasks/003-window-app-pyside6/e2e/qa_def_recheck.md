# QA: перепроверка DEF-001..003 после фикса (FIX-READY)

Дата: 2026-09-10T20:26:46+03:00

## Фикс на месте? (git status + _positive_float)
?? ex_window_app_pyside6/main_window_app.py
--- grep math/isfinite ---
17:import math
37:def _positive_float(value: str) -> float:
46:    if not math.isfinite(seconds) or seconds <= 0:
65:        type=_positive_float,

## DEF-001 — --smoke-window inf
usage: python -m ex_window_app_pyside6.main_window_app [-h] [--smoke]
                                                       [--smoke-window [SECONDS]]
python -m ex_window_app_pyside6.main_window_app: error: argument --smoke-window: значение должно быть > 0: 'inf'
inf exit=2

## DEF-002 — --smoke-window nan
usage: python -m ex_window_app_pyside6.main_window_app [-h] [--smoke]
                                                       [--smoke-window [SECONDS]]
python -m ex_window_app_pyside6.main_window_app: error: argument --smoke-window: значение должно быть > 0: 'nan'
nan exit=2

## DEF-003 — --smoke-window 1e309
usage: python -m ex_window_app_pyside6.main_window_app [-h] [--smoke]
                                                       [--smoke-window [SECONDS]]
python -m ex_window_app_pyside6.main_window_app: error: argument --smoke-window: значение должно быть > 0: '1e309'
1e309 exit=2

## Регресс — некорректные значения
usage: python -m ex_window_app_pyside6.main_window_app [-h] [--smoke]
                                                       [--smoke-window [SECONDS]]
python -m ex_window_app_pyside6.main_window_app: error: argument --smoke-window: значение должно быть > 0: '-1'
-1 exit=2
usage: python -m ex_window_app_pyside6.main_window_app [-h] [--smoke]
                                                       [--smoke-window [SECONDS]]
python -m ex_window_app_pyside6.main_window_app: error: argument --smoke-window: не число: 'abc'
abc exit=2

## Регресс — валидные режимы
smoke ok
--smoke exit=0
This plugin does not support propagateSizeHints()
--smoke-window 3 exit=0
duration=3,57s

## ruff
All checks passed!
ruff exit=0
