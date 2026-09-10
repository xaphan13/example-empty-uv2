# Оконный пример на PySide6 (Qt6): два поля ввода и две кнопки

Новый учебный пример-пакет в корне проекта: небольшое оконное приложение на Qt6 для Python — ровно два поля ввода текста и ровно две кнопки. Это тот же класс задачи, что у закрытого примера `002-window-app-customtkinter`, но намеренно на другом стеке: дублирование примеров «одна задача — разные подходы» в проекте приветствуется. Пример следует соглашениям проекта: каталог `ex_*`, точка входа `main_*.py`, ruff/black, русские комментарии и docstring'и, отсутствие тестов, проверка headless-запуском.

Источник — сырая идея пользователя, дословно: «нужно сделать новый пакедж и создать там приложение оконное на пайтон и qt6 - небольшое пара кнопок и пара вводов текста».

## Подтверждённые решения

- Идея пользователя (дословно): «нужно сделать новый пакедж и создать там приложение оконное на пайтон и qt6 - небольгое пара кнопок и пара вводов текста» (в тексте идеи — «небольшое пара кнопок и пара вводов текста»).
- Объём строго минимальный: **два** поля ввода и **две** кнопки; никаких тем, анимаций, сайдбаров, реестров примеров, второго окна и настроек.
- Qt-биндинг — **PySide6** (рекомендация spec-writer; подлежит подтверждению пользователем, см. открытый вопрос 1). Обоснование: лицензия LGPL против GPL/коммерческой у PyQt6, официальный проект «Qt for Python» от самой Qt, колёса на PyPI под Python 3.12 — отдельная сборка не нужна.
- Имя пакета — `ex_window_app_pyside6`, точка входа — `main_window_app.py` (говорящее самодокументирующее имя, как у соседнего GUI-примера). При выборе PyQt6 имя пакета меняется на `ex_window_app_pyqt6`, план фаз и контракт остаются те же, меняются только импорты `PySide6.*` → `PyQt6.*`.
- Разметка — **только кодом**, без pygubu и `.ui`-файла: pygubu работает исключительно с tkinter и здесь неприменим.
- Пример **не регистрируется в `main.py`** — как и соседний `ex_window_app_customtkinter`: открытое окно заблокировало бы общий прогон `python main.py`.
- Логирование через `config_log.logF` **не подключается**: пример демонстрирует только Qt. Это согласуется с соседним `ex_window_app_customtkinter`, который тоже не тянет `config_log`.
- Headless-проверка — через платформенный плагин Qt `QT_QPA_PLATFORM=offscreen` (входит в поставку PySide6): реальный дисплей и Xvfb не нужны.
- Существующие зависимости (`customtkinter`, `pygubu`, `pillow`, `rich`, `sshtunnel`, `streamz`, `aiosqlite`, `ruff`, `black`) не удаляются и не переписываются.

## Результат

После задания в репозитории должны существовать:

- `pyproject.toml` и `uv.lock` с runtime-зависимостью `pyside6`.
- Пакет `ex_window_app_pyside6/`:
  - `__init__.py` — маркер пакета, docstring на русском, без импортов GUI;
  - `application_window.py` — класс `ApplicationWindow(QWidget)`: два `QLineEdit`, два `QPushButton`, одна `QLabel` результата;
  - `main_window_app.py` — точка входа: обычный запуск, `--smoke`, `--smoke-window [СЕКУНДЫ]`.
- Обновлённые `docs/01_project_structure.md` и `docs/02_examples_overview.md` — правит оркестратор (см. раздел ниже), не разработчик.

Поведение:

- Обычный запуск открывает небольшое окно с заголовком «PySide6 — пример окна»: подпись и поле «Имя», подпись и поле «Сообщение», кнопки «Показать» и «Очистить», метка результата.
- Кнопка «Показать» собирает строку `«<имя>: <сообщение>»` и записывает её в метку результата; если оба поля пусты — в метке появляется «Введите имя и сообщение».
- Кнопка «Очистить» очищает оба поля ввода и возвращает метку результата в «—».
- `QT_QPA_PLATFORM=offscreen uv run python -m ex_window_app_pyside6.main_window_app --smoke` собирает окно, проверяет наличие виджетов, печатает `smoke ok` и завершается с кодом 0 (окно не показывается).
- `QT_QPA_PLATFORM=offscreen uv run python -m ex_window_app_pyside6.main_window_app --smoke-window 3` показывает окно и закрывает его через 3 секунды, код возврата 0.
- Импорт любого модуля пакета не создаёт `QApplication` и не открывает окно.

## Задачи оркестратора (вне фаз разработчика)

- `docs/01_project_structure.md`: добавить `ex_window_app_pyside6/` в дерево проекта и `pyside6` в список основных зависимостей (рядом с `customtkinter`).
- `docs/02_examples_overview.md`: добавить раздел про новый пример — команда запуска `python -m ex_window_app_pyside6.main_window_app`, два headless-режима (`--smoke`, `--smoke-window`), явная пометка, что пример не входит в `main.py`.
- Папку `docs/` субагентам редактировать запрещено (AGENTS.md); эти две правки делает только оркестратор и включает их в финальные критерии.

## Вне рамок

- Не использовать pygubu и `.ui`-файлы: разметка только кодом.
- Не делать реестр запускаемых примеров, `example_runner.py`, захват stdout/stderr и запуск чего-либо в фоновом потоке.
- Не добавлять `example_runner.py`, `window_app.ui` и прочие файлы соседнего `ex_window_app_customtkinter`.
- Не изменять `main.py`, `config_log.py`, `config_multi_proc_log.py` и существующие пакеты `ex_*`.
- Не добавлять в `main.py` регистрацию нового примера.
- Не писать тесты и не добавлять тестовые фреймворки.
- Не добавлять другие GUI/иконные/стилевые зависимости (`PyQt6`, `qtawesome`, `qt-material` и т. п.) сверх выбранного биндинга.
- Не подключать `config_log`/логирование и не писать лог-файлы.
- Не делать тёмных тем, переключателей темы, анимаций, hover-эффектов, иконок, меню, статус-баров, диалогов сохранения файла.
- Не реализовывать сохранение введённого текста на диск или в буфер обмена.

## План фаз

Единица исполнения — фаза: одно делегирование, 1–3 файла, бюджет ~10–15 ходов. Следующая фаза стартует только после зелёного checkpoint и ревью диффа оркестратором. Прогресс фазы разработчик фиксирует в `tasks/current/dev/phaseNN_progress.md`.

| # | Фаза | Исполнитель | Файлы | Контракт | Checkpoint | Бюджет ходов |
|---|---|---|---|---|---|---|
| 1 | Зависимость Qt6 | backend-dev | `pyproject.toml`, `uv.lock` | добавить runtime-зависимость `pyside6`, ничего не удалять | `uv run python -c "import PySide6; from PySide6.QtCore import qVersion; print('Qt', qVersion())"` → exit 0, `Qt 6.x.y` | ~6 |
| 2 | Пакет и окно | backend-dev | `ex_window_app_pyside6/__init__.py`, `ex_window_app_pyside6/application_window.py` | `ApplicationWindow(QWidget)`; замороженные objectName: `application_window`, `name_input`, `message_input`, `show_button`, `clear_button`, `result_label` | ruff + offscreen-конструирование окна с печатью objectName и двух кликов → exit 0 | ~14 |
| 3 | Точка входа и smoke | backend-dev | `ex_window_app_pyside6/main_window_app.py` | `main(argv) -> int`, `_build_parser()`, флаги `--smoke` и `--smoke-window SECONDS`; `QApplication` только внутри `main()` | ruff + `--smoke` (печатает `smoke ok`) + `--smoke-window 3` → оба exit 0 | ~12 |

### Фаза 1: Зависимость Qt6

- Файлы: `pyproject.toml`, `uv.lock`.
- Контракт:
  - В `[project].dependencies` добавляется `pyside6` (команда `uv add pyside6`; точная версия фиксируется в `uv.lock`, ожидаемо 6.8+).
  - Никакие существующие зависимости не удаляются и не переписываются вручную.
  - Dev-группа не трогается.
- Шаги:
  1. `uv add pyside6`.
  2. `uv sync`, убедиться, что `.venv` собрался.
  3. Проверить, что `pyside6` появился в `[project].dependencies` и в `uv.lock`.
- Checkpoint:
  ```bash
  uv run python -c "import PySide6; from PySide6.QtCore import qVersion; print('Qt', qVersion())"
  ```
  Ожидание: exit 0, в stdout `Qt 6.x.y`. Отсутствие ошибки импорта подтверждает, что колёса под Python 3.12 встали.
- Готовность фазы: зависимость зафиксирована в `pyproject.toml` и `uv.lock`, импорт работает.
- Риск: колёса PySide6 крупные (сотни МБ) — скачивание может занять время; если `uv add` не находит колесо под 3.12, это стоп-сигнал и повод вернуться к открытому вопросу 1 (PyQt6).

### Фаза 2: Пакет и окно

- Файлы: `ex_window_app_pyside6/__init__.py`, `ex_window_app_pyside6/application_window.py`.
- Контракт (замораживается для фазы 3):
  - `__init__.py`: docstring пакета на русском, никаких импортов GUI и никакого кода.
  - `application_window.py`: `from __future__ import annotations`; импорты `PySide6.QtWidgets` на уровне модуля; класс `ApplicationWindow(QWidget)`; конструктор `__init__(self, parent: QWidget | None = None) -> None` — внутри `setWindowTitle("PySide6 — пример окна")`, `setObjectName("application_window")`, вызов `self._build_layout()`.
  - Атрибуты и их `objectName` (имена заморожены, на них опираются checkpoint и qa):
    - `self.name_input: QLineEdit` → `name_input`, подпись «Имя»;
    - `self.message_input: QLineEdit` → `message_input`, подпись «Сообщение»;
    - `self.show_button: QPushButton` → `show_button`, текст «Показать»;
    - `self.clear_button: QPushButton` → `clear_button`, текст «Очистить»;
    - `self.result_label: QLabel` → `result_label`, стартовый текст «—».
  - Методы: `_build_layout(self) -> None` (один `QVBoxLayout`: подпись+поле «Имя», подпись+поле «Сообщение», строка с двумя кнопками, метка результата), `_on_show_clicked(self) -> None`, `_on_clear_clicked(self) -> None`.
  - Поведение: `_on_show_clicked` формирует `f"{name}: {message}"` и пишет в `result_label`; если оба поля пусты — текст «Введите имя и сообщение». `_on_clear_clicked` очищает оба поля и ставит в метку «—».
  - Сигналы привязываются в `__init__` через `clicked.connect(...)`.
  - Импорт модуля не создаёт `QApplication` и не создаёт виджетов.
  - Комментарии и docstring'и на русском, длина строки ≤ 120 (ruff-конфиг проекта).
- Шаги:
  1. Создать `__init__.py`.
  2. Создать `application_window.py` одним `write_file`.
  3. Проверить привязку сигналов и тексты.
  4. `uv run ruff check ex_window_app_pyside6/`.
- Checkpoint:
  ```bash
  uv run ruff check ex_window_app_pyside6/
  QT_QPA_PLATFORM=offscreen uv run python -c "
  from PySide6.QtWidgets import QApplication
  from ex_window_app_pyside6.application_window import ApplicationWindow
  app = QApplication([])
  w = ApplicationWindow()
  print(w.objectName(), w.name_input.objectName(), w.message_input.objectName(), w.show_button.objectName(), w.clear_button.objectName(), w.result_label.objectName())
  w.show_button.click()
  w.clear_button.click()
  print('ok')
  "
  ```
  Ожидание: ruff без ошибок; строка `application_window name_input message_input show_button clear_button result_label`; `ok`; exit 0; без traceback и без запроса дисплея.
- Готовность фазы: ruff чист, окно конструируется offscreen, все objectName на месте, оба клика отрабатывают без исключений.

### Фаза 3: Точка входа и smoke

- Файлы: `ex_window_app_pyside6/main_window_app.py`.
- Контракт (замораживается):
  - `main(argv: Sequence[str] | None = None) -> int`; `if __name__ == "__main__": raise SystemExit(main())`.
  - `_build_parser() -> argparse.ArgumentParser` с `prog="python -m ex_window_app_pyside6.main_window_app"`.
  - `--smoke` (`action="store_true"`): создать `QApplication`, создать `ApplicationWindow`, проверить наличие виджетов по objectName, напечатать `smoke ok`, вернуть 0; окно не показывать (`show()` не вызывается).
  - `--smoke-window [SECONDS]`: `nargs="?"`, `type=_positive_float` (значение строго > 0, иначе argparse exit 2), `const=5.0`, `default=False`; создать `QApplication` и окно, вызвать `show()`, запланировать закрытие через `QTimer.singleShot(int(seconds * 1000), app.quit)`, затем `app.exec()` и вернуть 0.
  - Одновременная передача `--smoke` и `--smoke-window` — сообщение в stderr и код возврата 2.
  - Без флагов — обычный запуск: окно показывается, `app.exec()`.
  - `QApplication` создаётся только внутри `main()`; на уровне модуля GUI-объектов нет.
  - Docstring модуля описывает три режима, комментарии на русском, длина строки ≤ 120.
- Шаги:
  1. Создать `main_window_app.py` одним `write_file`.
  2. `uv run ruff check ex_window_app_pyside6/`.
  3. Прогнать оба offscreen-режима.
- Checkpoint:
  ```bash
  uv run ruff check ex_window_app_pyside6/
  QT_QPA_PLATFORM=offscreen uv run python -m ex_window_app_pyside6.main_window_app --smoke
  QT_QPA_PLATFORM=offscreen uv run python -m ex_window_app_pyside6.main_window_app --smoke-window 3
  ```
  Ожидание: ruff без ошибок; первая команда печатает `smoke ok` и завершается с кодом 0; вторая завершается с кодом 0 примерно через 3 секунды, без traceback и без подвисания.
- Готовность фазы: оба headless-режима зелёные, обычный запуск описан в docstring.

## Критерии успеха

Проверяются qa по завершении всех фаз; сырые выводы — в `tasks/current/e2e/`.

| # | Критерий | Проверка | Ожидание |
|---|---|---|---|
| 1 | Зависимость Qt6 установлена | `uv run python -c "import PySide6; from PySide6.QtCore import qVersion; print('Qt', qVersion())"` | exit 0, строка `Qt 6.x.y` |
| 2 | Ruff чист по всему проекту | `uv run ruff check .` | нет ошибок |
| 3 | Пакет импортируется headless | `QT_QPA_PLATFORM=offscreen uv run python -c "from ex_window_app_pyside6.application_window import ApplicationWindow; print('import ok')"` | exit 0, `import ok`, `QApplication` не создаётся |
| 4 | Состав окна ровно по заданию | `grep -c "QLineEdit(" ex_window_app_pyside6/application_window.py` и `grep -c "QPushButton(" ex_window_app_pyside6/application_window.py` | 2 и 2 соответственно |
| 5 | Все objectName из контракта на месте | `QT_QPA_PLATFORM=offscreen uv run python -m ex_window_app_pyside6.main_window_app --smoke` | exit 0, stdout `smoke ok` |
| 6 | Окно поднимается и закрывается без дисплея | `QT_QPA_PLATFORM=offscreen uv run python -m ex_window_app_pyside6.main_window_app --smoke-window 3` | exit 0, без traceback, длительность ~3 с |
| 7 | Некорректные аргументы дают exit 2 без traceback | `QT_QPA_PLATFORM=offscreen uv run python -m ex_window_app_pyside6.main_window_app --smoke-window 0` | exit 2, понятное сообщение в stderr |
| 8 | Существующие примеры не задеты | `git diff --name-only` | среди изменённых нет `main.py`, `config_log.py`, `ex_window_app_customtkinter/*`, других `ex_*/` |
| 9 | Документация обновлена (правка оркестратора) | `grep -q "ex_window_app_pyside6" docs/01_project_structure.md && grep -q "ex_window_app_pyside6" docs/02_examples_overview.md` | обе команды возвращают 0 |

## Финальные критерии

1. Каждый критерий успеха подтверждён доказательством (e2e/, DEFECTS.md,
   ADVERSARIAL_REVIEW.md).
2. `tasks/current/DEFECTS.md` существует только если найдены дефекты; все записи
   не OPEN.
3. Adversarial-прогон выполнен, ни одна запись ADVERSARIAL_REVIEW.md не PENDING.

## Открытые вопросы

Открытых вопросов нет — все закрыты оркестратором 2026-09-10 (режим без
подтверждений, решения исполнителя с фиксацией здесь). Ответы перенесены
в «Подтверждённые решения» выше:

- Qt-биндинг — **PySide6** (рекомендация spec-writer принята): LGPL вместо
  GPL/коммерческой, официальный «Qt for Python», колёса под Python 3.12.
  Имя пакета — `ex_window_app_pyside6`, импорты `PySide6.*`.
- Кнопки — **минимальный вариант**: «Показать» пишет в метку `«<имя>: <сообщение>»`,
  при обоих пустых полях — «Введите имя и сообщение»; «Очистить» очищает оба поля
  и возвращает метку в «—».
- Подписи и заголовки приняты как есть: «Имя», «Сообщение», «Показать», «Очистить»,
  заголовок окна «PySide6 — пример окна».
- Регистрация в `main.py` — **нет** (как у `ex_window_app_customtkinter`: открытое
  окно заблокировало бы общий прогон `python main.py`).

Замечание по line-length: `pyproject.toml` задаёт `line-length = 120`, AGENTS.md
декларирует «ruff 100». Приоритет — фактический конфиг (`120`); правку AGENTS.md
вне рамок этого задания не делаем.

---

# Отчёт о выполнении

- Дата закрытия: 2026-09-10
- Коммит: не коммитилось (изменения в рабочем дереве, ветка `task-new-custom`)

## Итог
Создан новый учебный пример `ex_window_app_pyside6/` — минимальное оконное приложение
на PySide6 (Qt6): два поля ввода, две кнопки, метка результата, три режима запуска.
Работоспособность подтверждена offscreen-прогонами qa (все 9 критериев PASS) и
adversarial-прогоном; три найденных Major-дефекта валидации `--smoke-window`
исправлены и закрыты qa.

## Изменения
- `pyproject.toml` → добавлена runtime-зависимость `pyside6>=6.11.2`.
- `uv.lock` → зафиксированы `pyside6==6.11.2`, `pyside6-addons`, `pyside6-essentials`, `shiboken6`.
- `ex_window_app_pyside6/__init__.py` → новый, маркер пакета, docstring на русском.
- `ex_window_app_pyside6/application_window.py` → новый, класс `ApplicationWindow(QWidget)`: два `QLineEdit`, два `QPushButton`, `QLabel` результата, замороженные objectName.
- `ex_window_app_pyside6/main_window_app.py` → новый, точка входа: обычный запуск, `--smoke`, `--smoke-window [SECONDS]`; `_positive_float` с проверкой `math.isfinite`.
- `docs/01_project_structure.md` → дерево проекта и список зависимостей (правка оркестратора).
- `docs/02_examples_overview.md` → команды запуска и описание примера (правка оркестратора).

## Критерии успеха
| # | Критерий | Результат | Доказательство |
|---|---|---|---|
| 1 | Зависимость Qt6 установлена | PASS | e2e/qa_success_criteria.md (C1: `Qt 6.11.2`, exit 0) |
| 2 | Ruff чист по всему проекту | PASS | e2e/qa_success_criteria.md (C2), e2e/qa_def_recheck.md |
| 3 | Пакет импортируется headless, без `QApplication` | PASS | e2e/qa_success_criteria.md (C3: `import ok`) |
| 4 | Состав окна: 2×`QLineEdit`, 2×`QPushButton` | PASS | e2e/qa_success_criteria.md (C4: 2 и 2) |
| 5 | Все objectName на месте (`--smoke`) | PASS | e2e/qa_success_criteria.md (C5: `smoke ok`, exit 0) |
| 6 | Окно поднимается и закрывается без дисплея | PASS | e2e/qa_success_criteria.md (C6: exit 0, ~3,34 с) |
| 7 | Некорректные аргументы → exit 2 без traceback | PASS | e2e/qa_def_recheck.md (`inf`/`nan`/`1e309`/`-1`/`abc` → exit 2) |
| 8 | Существующие примеры не задеты | PASS | e2e/qa_success_criteria.md (C8: `git diff`/`git status` без чужих `ex_*`) |
| 9 | Документация обновлена | PASS | e2e/qa_success_criteria.md (C9: оба grep вернули 0) |
| Доп. | Поведение окна (метка результата, очистка) | PASS | e2e/qa_success_criteria.md (Extra: `Иван: привет`, «Введите имя и сообщение», `—`) |

## Дефекты
Найдены 3 дефекта (все Major), все закрыты:
- DEF-001 `--smoke-window inf` → CLOSED (e2e/qa_adv_repro.md, e2e/qa_def_recheck.md)
- DEF-002 `--smoke-window nan` → CLOSED (e2e/qa_adv_repro.md, e2e/qa_def_recheck.md)
- DEF-003 `--smoke-window 1e309` → CLOSED (e2e/qa_adv_repro.md, e2e/qa_def_recheck.md)

Исправление: `_positive_float` в `main_window_app.py` — добавлена проверка
`not math.isfinite(seconds) or seconds <= 0`. Все три сценария перепроверены qa:
exit 2, traceback отсутствует; регресс и ruff зелёные.

## Adversarial-прогон
ADV-001: ACCEPTED -> DEF-001 · ADV-002: ACCEPTED -> DEF-002 · ADV-003: ACCEPTED -> DEF-003 ·
ADV-004: REJECTED — верхняя граница `--smoke-window` спекой не задана · ADV-005: REJECTED —
подтверждение `const=5.0` · ADV-006: REJECTED — задокументированная cwd-грабля (AGENTS.md) ·
ADV-007: REJECTED — спека говорит про «пусты» поля, про пробельные значения контракт молчит ·
ADV-008: REJECTED — штатный обычный режим (`app.exec()`). PENDING-записей нет.

## Участники
- spec-writer: спека REQUIREMENTS.md с планом фаз (PySide6 выбран по лицензии LGPL).
- backend-dev: фазы 1–3 (зависимость, пакет+окно, точка входа) и фикс DEF-001..003.
- qa: прогон 9 критериев + поведение окна, воспроизведение и закрытие DEF-001..003.
- adversary: враждебный прогон границ `--smoke-window`, конфликтов флагов, импорта, идемпотентности.
- оркестратор: триаж ADV, правки `docs/`, архивация задания.