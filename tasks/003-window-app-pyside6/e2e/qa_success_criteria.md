# QA: прогон критериев успеха — оконный пример PySide6

Дата: 2026-09-10T19:55:03+03:00
cwd: /home/max/0_0_26_new_one/example-empty-uv2

## C1 — PySide6 установлен
Qt 6.11.2
exit=0

## C2 — ruff по всему проекту
All checks passed!
exit=0

## C3 — headless импорт пакета
import ok
exit=0

## C4 — состав окна (grep -c)
QLineEdit count: 2
exit=0
QPushButton count: 2
exit=0

## C5 — --smoke
smoke ok
exit=0

## C6 — --smoke-window 3
This plugin does not support propagateSizeHints()
exit=0
duration=3,34s

## C7 — --smoke-window 0 (некорректно)
usage: python -m ex_window_app_pyside6.main_window_app [-h] [--smoke]
                                                       [--smoke-window [SECONDS]]
python -m ex_window_app_pyside6.main_window_app: error: argument --smoke-window: значение должно быть > 0: '0'
exit=2

## C8 — git diff / status
$ git diff --name-only
.qwen/agents/adversary.md
.qwen/agents/backend-dev.md
.qwen/agents/frontend-dev.md
.qwen/agents/qa.md
.qwen/agents/spec-writer.md
docs/01_project_structure.md
docs/02_examples_overview.md
pyproject.toml
tasks/current/REQUIREMENTS.md
uv.lock
--- git status --short ---
 M .qwen/agents/adversary.md
 M .qwen/agents/backend-dev.md
 M .qwen/agents/frontend-dev.md
 M .qwen/agents/qa.md
 M .qwen/agents/spec-writer.md
 M docs/01_project_structure.md
 M docs/02_examples_overview.md
 M pyproject.toml
 M tasks/current/REQUIREMENTS.md
 M uv.lock
?? ex_window_app_pyside6/
?? tasks/current/dev/
?? tasks/current/e2e/

## C9 — docs
docs/01 grep exit=0
docs/02 grep exit=0

## Extra — поведение окна (offscreen)
case1 label: 'Иван: привет'
after clear: name= '' message= '' label= '—'
case2 empty label: 'Введите имя и сообщение'
case3 after clear label: '—'
behavior ok
exit=0
