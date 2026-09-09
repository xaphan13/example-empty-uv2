# Phase 01 — Замена ttkbootstrap на customtkinter в runtime-зависимостях

Дата: 2026-09-09
Агент: backend-dev

## План

1. Создать `tasks/current/dev/`.
2. `uv remove ttkbootstrap` — убрать из dependencies и перегенерировать uv.lock.
3. `uv add "customtkinter>=5.2.0"` — добавить в dependencies и перегенерировать uv.lock.
4. Checkpoint: `uv sync`, импорт customtkinter и pygubu, грепом убедиться что ttkbootstrap отсутствует в обоих файлах.
5. Сырые выводы — в `phase01_raw.txt`.

## Прогресс

### 2026-09-09 — старт

- Прочитал AGENTS.md (зоны, проверки, запреты), спецификацию фазы.
- Прочитал `pyproject.toml`: `ttkbootstrap>=2.2.2` присутствует в `[project].dependencies`,
  `pygubu>=0.42.1` присутствует, dev-группа `pygubu-designer>=0.46.1` присутствует.
- `grep -i ttkbootstrap pyproject.toml uv.lock` подтверждает наличие (5 строк в uv.lock, 1 в pyproject.toml).
- Стартовый checkpoint выполнен и зафиксирован.

### 2026-09-09 — шаг 1: `uv remove ttkbootstrap`

Команда: `uv remove ttkbootstrap`
Результат: exit 0
- Resolved 39 packages in 3.85s
- Uninstalled 2 packages: `pillow==12.3.0`, `ttkbootstrap==2.2.2`
- `pillow` ушёл как зависимость `ttkbootstrap` (транзитивная пакетная зависимость),
  он не указан в `[project].dependencies` напрямую — это ожидаемое поведение uv
  при удалении пакета, тянувшего pillow.
- Сырой вывод: `phase01_raw.txt`.
- Статус: PASS.

### 2026-09-09 — шаг 2: `uv add "customtkinter>=5.2.0"`

Команда: `uv add "customtkinter>=5.2.0"`
Результат: exit 0
- Resolved 41 packages in 2.88s
- Prepared 2 packages, Installed 2 packages
- Установлены: `customtkinter==6.0.0`, `darkdetect==0.8.0` (транзитивная зависимость customtkinter).
- `customtkinter==6.0.0` удовлетворяет спецификатору `>=5.2.0` (на момент фиксации uv
  в реестре PyPI новейшая стабильная — 6.0.0; 5.2.x тоже бы подошёл).
- Сырой вывод: `phase01_raw.txt` (дописан в режиме `-a`).
- Статус: PASS.

### 2026-09-09 — промежуточная проверка после шагов 1+2

Команда: `grep -n ttkbootstrap pyproject.toml uv.lock; grep -n customtkinter pyproject.toml uv.lock; grep -n '"pygubu"' pyproject.toml uv.lock; grep -n '"pillow"' pyproject.toml uv.lock`
- ttkbootstrap: пусто (в обоих файлах)
- customtkinter: присутствует (нужно подтвердить в финальном checkpoint)
- pygubu с specifier `>=0.42.1`: на месте
- pillow в [project].dependencies: не было и нет
Статус: промежуточно PASS, ждём финального checkpoint.

### 2026-09-09 — финальный checkpoint (закрытие фазы)

Команда 1: `uv sync`
- `Resolved 41 packages in 1ms`, `Checked 36 packages in 0.57ms`
- Exit 0
Статус: PASS

Команда 2 (дословно из спецификации): `uv run python -c "import customtkinter as ctk, pygubu; print(ctk.__version__, pygubu.__version__)"`
- Traceback: `AttributeError: module 'pygubu' has no attribute '__version__'`
- Exit 1
- **Расследование:** у `pygubu` нет top-level атрибута `__version__` — это свойство самой
  библиотеки (`pygubu` не объявляет `__version__` в `__init__.py`). У `customtkinter`
  `__version__` есть (`6.0.0`).
- **Рабочая альтернатива:** `import importlib.metadata as m; m.version('customtkinter')`
  / `m.version('pygubu')` — стандартный способ для Python ≥ 3.8.
  Доп. проверка: `customtkinter 6.0.0`, `pygubu 0.42.1`, exit 0.
- Это не дефект фазы 1 (зависимости): спецификация дала одну строку, реальность
  библиотеки pygubu — другая. Подсвечу оркестратору для решения: оставить как есть
  в checkpoint'е (importlib.metadata) или вернуть спецификацию к правде.

Команда 3: `grep -i ttkbootstrap pyproject.toml uv.lock`
- Пусто (exit 1 — grep не нашёл совпадений, это и есть ожидание).
Статус: PASS

### Итог фазы 1

- pyproject.toml: ttkbootstrap удалён, customtkinter>=5.2.0 на месте, pygubu>=0.42.1
  и dev pygubu-designer>=0.46.1 без изменений.
- uv.lock: ttkbootstrap отсутствует, customtkinter 6.0.0 + транзитивный darkdetect
  добавлены, pygubu 0.42.1 без изменений.
- uv sync зелёный.
- import customtkinter работает (версия 6.0.0 доступна и через `ctk.__version__`,
  и через `importlib.metadata`).
- import pygubu работает (версия 0.42.1 — только через `importlib.metadata`).
- grep по ttkbootstrap в обоих манифестах пуст.

Замечание к оркестратору: checkpoint-строка спецификации
`import customtkinter as ctk, pygubu; print(ctk.__version__, pygubu.__version__)`
не работает из-за pygubu. Реальный рабочий вариант —
`import importlib.metadata as m; m.version('customtkinter'); m.version('pygubu')`.
Прошу решить: оставить ли в критериях успеха исходный `__version__` (тогда надо
менять спецификацию) или принять importlib.metadata-вариант.
