# Фаза 3 — Точка входа и smoke (backend-dev)

Дата: 2026-09-10
Файл фазы: `ex_window_app_pyside6/main_window_app.py` (новый, единственный).
Контракт: `main(argv: Sequence[str] | None = None) -> int`; `_build_parser()` с
`prog="python -m ex_window_app_pyside6.main_window_app"`; `--smoke` (`store_true`);
`--smoke-window [SECONDS]` (`nargs="?"`, `type=_positive_float`, `const=5.0`,
`default=False`); одновременная передача — stderr + exit 2; `QApplication` только
внутри `main()`; на уровне модуля GUI-объектов нет.

## Прогресс

- [x] Шаг 1. `main_window_app.py` — создан одним `write_file`
- [x] Шаг 2. `uv run ruff check ex_window_app_pyside6/` — exit 0, `All checks passed!`
- [x] Шаг 3. offscreen `--smoke` — stdout `smoke ok`, exit 0
- [x] Шаг 4. offscreen `--smoke-window 3` — exit 0, elapsed 4s (3 с таймер + старт)
- [x] Доп. негативные проверки: `--smoke-window 0` → exit 2; `--smoke --smoke-window 3` → exit 2

## Сырые выводы

Checkpoint целиком (`tasks/current/dev/phase03_checkpoint.txt`):

    === ruff ===
    All checks passed!
    ruff exit=0
    === smoke ===
    smoke ok
    smoke exit=0
    === smoke-window 3 ===
    This plugin does not support propagateSizeHints()
    smoke_window exit=0
    elapsed=4s
    === smoke-window 0 (expect 2) ===
    usage: python -m ex_window_app_pyside6.main_window_app [-h] [--smoke]
                                                           [--smoke-window [SECONDS]]
    python -m ex_window_app_pyside6.main_window_app: error: argument --smoke-window: значение должно быть > 0: '0'
    zero exit=2
    === both flags (expect 2) ===
    Нельзя одновременно использовать --smoke и --smoke-window
    both exit=2

Диагностика: traceback отсутствует; запроса дисплея нет (`QT_QPA_PLATFORM=offscreen`);
строка `This plugin does not support propagateSizeHints()` — штатное предупреждение
offscreen-платформы Qt, не ошибка. `--smoke-window 3` уложился в ~3 с таймера + ~1 с
на старт Qt.

## Итог

Фаза 3 завершена: создан единственный новый файл `ex_window_app_pyside6/main_window_app.py`.
Контракт соблюдён — `main(argv) -> int`, `_build_parser()` с `prog`, `--smoke`,
`--smoke-window [SECONDS]` с `_positive_float`/`const=5.0`/`default=False`,
одновременные флаги → stderr + exit 2, `QApplication` только внутри `main()`,
на уровне модуля GUI-объектов нет, `if __name__ == "__main__": raise SystemExit(main())`.
Ruff чист, оба offscreen-режима зелёные (exit 0). Файлы фаз 1–2 и прочие модули не
трогались. Блокеров нет.