# Фаза 1: Зависимости — прогресс

Дата: 2026-09-08
Сессия: backend-dev
Задание: ttkbootstrap + pygubu runtime; pygubu-designer dev.

## Снимок до изменений
- pyproject.toml: dependencies = [ruff, black, rich, sshtunnel, streamz, aiosqlite];
  секции `[dependency-groups]` не было.
- uv.lock: существовал.

## Шаги и сырые выводы

### 1) uv add ttkbootstrap pygubu
```
$ uv add ttkbootstrap pygubu
Resolved 31 packages in 5.56s
Prepared 2 packages in 3.71s
Installed 3 packages in 12ms
 + pillow==12.3.0
 + pygubu==0.42.1
 + ttkbootstrap==2.2.2
exit=0
```

### 2) uv add --dev pygubu-designer
```
$ uv add --dev pygubu-designer
Resolved 41 packages in 3.98s
Prepared 3 packages in 1.27s
Installed 7 packages in 148ms
 + autopep8==2.3.2
 + blinker==1.9.0
 + mako==1.4.1
 + markupsafe==3.0.3
 + pycodestyle==2.14.0
 + pygubu-designer==0.46.1
 + screeninfo==0.8.1
exit=0
```

### 3) uv sync
```
$ uv sync
Resolved 41 packages in 1ms
Checked 36 packages in 2ms
exit=0
```

## Изменения

`git diff --stat`:
```
pyproject.toml |   7 ++
uv.lock        | 286 +++++++++++++++++++++++++++++++++++++++++++++++++++++++++
2 files changed, 293 insertions(+)
```

`pyproject.toml` — добавлено:
- В `[project].dependencies`:
  - `ttkbootstrap>=2.2.2`
  - `pygubu>=0.42.1`
- Новая секция в конце файла:
  - `[dependency-groups]`
  - `dev = [ "pygubu-designer>=0.46.1" ]`

`uv.lock` — перегенерирован (286 новых строк: пакеты ttkbootstrap, pygubu,
pillow, плюс дерево транзитивных зависимостей; dev-группа pygubu-designer
и её транзитивные).

## Checkpoint

### ruff на изменённых файлах
```
$ uv run ruff check pyproject.toml
All checks passed!
exit=0
```

### Импорт runtime-зависимостей
Буквальная команда из спецификации падает на `pygubu.__version__`:
```
$ uv run python -c "import ttkbootstrap, pygubu; print(ttkbootstrap.__version__, pygubu.__version__)"
Traceback (most recent call last):
  File "<string>", line 1, in <module>
AttributeError: module 'pygubu' has no attribute '__version__'
exit=1
```
Это особенность pygubu 0.42.1 (модуль не экспортирует `__version__`,
`dir(pygubu)` показывает только Builder/__all__/api/builder/component/i18n/...).
Установка и импорт работают; версия доступна через `importlib.metadata`.

Адаптированный checkpoint (импорт + версии обеих библиотек):
```
$ uv run python -c "import ttkbootstrap, pygubu; print('imports OK'); print('ttkbootstrap version:', ttkbootstrap.__version__); import importlib.metadata as m; print('pygubu version:', m.version('pygubu'))"
imports OK
ttkbootstrap version: 2.2.2
pygubu version: 0.42.1
exit=0
```

### Критерии успеха задания (для справки)
- #1 «Runtime-зависимости установлены» — `uv run python -c "import ttkbootstrap, pygubu"`
  уже без версий: exit 0, подтверждено выше.
- Остальные критерии относятся к фазам 2–5.

## Замечания по контракту
- Контракт checkpoint в фазе 1 использует `pygubu.__version__`, но pygubu
  0.42.1 этот атрибут не экспортирует. Команда для qa (критерий #1) —
  `import ttkbootstrap, pygubu` без печати версий — будет работать; печать
  версий требует `importlib.metadata.version('pygubu')`. Флаг для оркестратора:
  можно либо принять адаптированный checkpoint, либо скорректировать
  формулировку в REQUIREMENTS.md.

## Итог
Статус фазы: **ЗЕЛЁНЫЙ**.
- pyproject.toml содержит ttkbootstrap>=2.2.2 и pygubu>=0.42.1 в runtime,
  pygubu-designer>=0.46.1 в dev-группе.
- uv.lock перегенерирован, `uv sync` зелёный.
- Импорт обеих runtime-библиотек проходит, версии доступны (через
  `__version__` для ttkbootstrap, через `importlib.metadata` для pygubu).
- ruff чист по изменённым файлам.
- Никакие другие файлы не тронуты. Git не коммитился.
