# Фаза 5 — Документация

## План

- `docs/01_project_structure.md`:
  - В дерево проекта добавить `ex_window_app_ttkbootstrap/` со списком модулей
    (`__init__.py`, `example_runner.py`, `application_window.py`,
    `main_window_app.py`, `window_app.ui`).
  - В раздел «Зависимости» добавить `ttkbootstrap` (runtime), `pygubu` (runtime),
    `pygubu-designer` (dev).
- `docs/02_examples_overview.md`:
  - В секцию «Через конкретные модули» добавить подсекцию `#### GUI на ttkbootstrap + pygubu`
    с командой запуска `python -m ex_window_app_ttkbootstrap.main_window_app`.
  - В секцию «Краткое описание каждого примера» добавить `### ex_window_app_ttkbootstrap`
    с описанием (GUI, ttkbootstrap + pygubu, запуск курируемых примеров с захватом вывода,
    тёмные темы, headless-режимы `--smoke` / `--smoke-window`).
- Прогресс-файл: `tasks/current/dev/phase05_progress.md`.
- Checkpoint: `grep -n "ex_window_app_ttkbootstrap" docs/01_project_structure.md`
  и `grep -n "main_window_app.py" docs/02_examples_overview.md` — обе exit 0.

## Прогресс

- 2026-09-08 — `docs/01_project_structure.md`: добавлен пакет
  `ex_window_app_ttkbootstrap/` в дерево (после `ex_all_others/`) с пятью
  файлами: `__init__.py`, `example_runner.py`, `application_window.py`,
  `main_window_app.py`, `window_app.ui`. В раздел «Зависимости» добавлены
  `ttkbootstrap` и `pygubu` (runtime) и подсекция «Dev-зависимости» с
  `pygubu-designer`. Статус: grep зелёный.
- 2026-09-08 — `docs/02_examples_overview.md`: в «Через конкретные модули»
  добавлена подсекция `#### GUI на ttkbootstrap + pygubu` с командами запуска
  (`main_window_app`, `--smoke`, `--smoke-window`) и замечанием про
  `main.py`. В «Краткое описание каждого примера» добавлен раздел
  `### ex_window_app_ttkbootstrap` с явным упоминанием
  `ex_window_app_ttkbootstrap/main_window_app.py` (точка входа), описанием
  захвата вывода, тёмных тем (`darkly`/`superhero`/`cyborg`/`solar`/`vapor`),
  фонового потока + `after()` и headless-режимов. Статус: grep зелёный.

## Checkpoint

```text
$ grep -n "ex_window_app_ttkbootstrap" docs/01_project_structure.md
92:    └── ex_window_app_ttkbootstrap/  # GUI-пример на ttkbootstrap + pygubu
109:- ttkbootstrap - тёмные темы оформления для Tk (используется в ex_window_app_ttkbootstrap)
110:- pygubu - загрузка XML-разметки интерфейса (используется в ex_window_app_ttkbootstrap)
exit=0

$ grep -n "main_window_app.py" docs/02_examples_overview.md
144:`ex_window_app_ttkbootstrap/main_window_app.py`:
exit=0
```

Сырой вывод: `tasks/current/dev/phase05_grep.txt`.

## Статус

Фаза 5 завершена. Оба grep'а из спецификации возвращают 0, документация
обновлена минимальными точечными вставками, стиль и форматирование
сохранены. Изменены только два указанных файла; `pyproject.toml`, README,
`tasks/current/REQUIREMENTS.md`, `.qwen/` и пакет `ex_window_app_ttkbootstrap/`
не трогались.
