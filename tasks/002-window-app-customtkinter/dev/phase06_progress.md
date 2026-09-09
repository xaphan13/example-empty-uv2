# Фаза 6 — Документация (backend-dev)

Дата: 2026-09-09.
Зона: `docs/01_project_structure.md`, `docs/02_examples_overview.md`, `tasks/current/dev/phase06_*`.
Контракт: имя пакета `ex_window_app_customtkinter`, зависимости `customtkinter` + `pillow`,
`pygubu` и dev-`pygubu-designer` остаются, `ttkbootstrap` упоминаться не должен.

## План
1. `docs/01_project_structure.md`:
   - в дереве заменить запись `ex_window_app_ttkbootstrap/ ...` на `ex_window_app_customtkinter/ ...`
     с актуальным списком файлов.
   - в списке зависимостей убрать `ttkbootstrap`, добавить `customtkinter` (UI-библиотека) и
     `pillow` (требование плагина `pygubu.plugins.customtkinter`); `pygubu` и dev-`pygubu-designer`
     остаются.
2. `docs/02_examples_overview.md`:
   - обновить имя пакета и команды запуска (обычный запуск, `--smoke`, `--smoke-window`).
   - переписать описание GUI-примера: CustomTkinter, тёмная тема, сайдбар+контент, карточки,
     акцентная кнопка «Запустить», прогресс-индикатор, статусная строка, разметка через
     pygubu Builder + плагин `pygubu.plugins.customtkinter`.
3. Прогнать checkpoint-команды.

## Чекпоинт
- `grep -q "ex_window_app_customtkinter" docs/01_project_structure.md` → 0
- `grep -q "ex_window_app_customtkinter/main_window_app.py" docs/02_examples_overview.md` → 0
- `grep -q "customtkinter" docs/01_project_structure.md` → 0
- `! grep -q "ex_window_app_ttkbootstrap" docs/01_project_structure.md` → 1
- `! grep -q "ex_window_app_ttkbootstrap" docs/02_examples_overview.md` → 1

Все 5 checkpoint-ов зелёные. Дополнительно широкая проверка
`grep -n "ttkbootstrap" docs/01_project_structure.md docs/02_examples_overview.md`
тоже возвращает 1 (подстрока `ttkbootstrap` нигде в двух файлах не встречается).

## Изменения

### docs/01_project_structure.md
- Дерево: запись `ex_window_app_ttkbootstrap/ ...` переименована в
  `ex_window_app_customtkinter/ ...`, комментарий «GUI-пример на CTk + pygubu»,
  описание `window_app.ui` уточнено «XML-разметка Pygubu на CTk-виджетах».
- Список зависимостей: `ttkbootstrap` удалён, добавлены `customtkinter`
  (UI-библиотека на CTk-виджетах) и `pillow` (обязательная зависимость
  плагина `pygubu.plugins.customtkinter`, на уровне `ctkbase.py` —
  безусловный `from PIL import ...`); `pygubu` и dev-`pygubu-designer`
  сохранены.

### docs/02_examples_overview.md
- Заголовок секции запуска: «GUI на CustomTkinter + pygubu».
- Команды запуска: `python -m ex_window_app_customtkinter.main_window_app`
  (обычный запуск), плюс `--smoke [имя_примера]` и `--smoke-window [секунды]`
  с тем же синтаксисом.
- Описание примера (`### ex_window_app_customtkinter`) полностью переписано
  под CTk: тёмная статичная тема, сайдбар слева с заголовком «Примеры»,
  полем поиска, `CTkScrollableFrame` из 5 карточек; контент справа —
  текстбокс-«терминал», кнопка «Запустить» с акцентом, кнопка «Очистить»,
  прогресс-индикатор, статусная строка; выбор примера — кликом по карточке;
  разметка `window_app.ui` через pygubu Builder + плагин
  `pygubu.plugins.customtkinter`; оставлены: запуск 5 курируемых примеров
  из окна, захват stdout/stderr/логов, `threading` + `queue` + `window.after`,
  headless-режимы, причина исключения из `main.py`.

## Замечания по контракту
- Help-текст `python -m ex_window_app_customtkinter.main_window_app --help`
  всё ещё говорит «GUI-примера на ttkbootstrap + pygubu» — это в зоне фазы 5
  (код), не моей; не правил.
