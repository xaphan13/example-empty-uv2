# Фаза 2 — Пакет и окно (backend-dev)

Дата: 2026-09-10
Файлы фазы: `ex_window_app_pyside6/__init__.py`, `ex_window_app_pyside6/application_window.py`
Контракт: `ApplicationWindow(QWidget)`; замороженные objectName `application_window`,
`name_input`, `message_input`, `show_button`, `clear_button`, `result_label`;
сигналы привязываются в `__init__`; импорт модуля не создаёт `QApplication` и виджетов.

## Прогресс

- [x] Шаг 1. `__init__.py` — создан: docstring пакета на русском, без импортов GUI и кода
- [x] Шаг 2. `application_window.py` — создан: `ApplicationWindow(QWidget)`, один `QVBoxLayout`,
      два `QLineEdit`, два `QPushButton`, `QLabel`; сигналы привязаны в `__init__`
- [x] Шаг 3. `uv run ruff check ex_window_app_pyside6/` — exit 0, `All checks passed!`
- [x] Шаг 4. Checkpoint — exit 0, строка objectName и `ok`; сырой вывод — `phase02_checkpoint.txt`

## Сырые выводы

Checkpoint целиком (`tasks/current/dev/phase02_checkpoint.txt`):

    === ruff ===
    All checks passed!
    ruff exit=0
    === checkpoint ===
    application_window name_input message_input show_button clear_button result_label
    ok
    checkpoint exit=0

Диагностика: traceback отсутствует, запроса дисплея нет (`QT_QPA_PLATFORM=offscreen`),
оба клика (`show_button.click()`, `clear_button.click()`) отработали без исключений.

## Итог

Фаза 2 завершена: пакет `ex_window_app_pyside6/` создан двумя новыми файлами.
Контракт соблюдён — objectName `application_window`, `name_input`, `message_input`,
`show_button`, `clear_button`, `result_label` на месте; импорт модуля не создаёт
`QApplication` и виджетов. Ruff чист, offscreen-checkpoint зелёный (exit 0).
Файлы других фаз не создавались. Блокеров нет.