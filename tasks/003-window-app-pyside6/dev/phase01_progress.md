# Фаза 1 — Зависимость Qt6 (backend-dev)

Дата: 2026-09-10
Файлы фазы: `pyproject.toml`, `uv.lock`
Контракт: добавить runtime-зависимость `pyside6` через `uv add pyside6`; существующие
зависимости не удалять и не переписывать вручную; `[dependency-groups] dev` не трогать.

## Прогресс

- [x] Шаг 1. `uv add pyside6` — установлено 4 пакета (pyside6 6.11.2, pyside6-addons,
      pyside6-essentials, shiboken6); сырой вывод — `phase01_uv_add.txt`
- [x] Шаг 2. `uv sync` — exit 0; сырой вывод — `phase01_uv_sync.txt`
- [x] Шаг 3. `pyside6` есть в `pyproject.toml` (строка 19: `"pyside6>=6.11.2",`) и в
      `uv.lock` (23 вхождения)
- [x] Checkpoint — exit 0, stdout `Qt 6.11.2`; сырой вывод — `phase01_checkpoint.txt`

## Сырые выводы

`uv add pyside6` (tail):

    Resolved 46 packages in 5.99s
    Downloading pyside6-essentials (76.4MiB)
    Downloading pyside6-addons (167.0MiB)
    Prepared 4 packages in 37.23s
    Installed 4 packages in 110ms
     + pyside6==6.11.2
     + pyside6-addons==6.11.2
     + pyside6-essentials==6.11.2
     + shiboken6==6.11.2

`uv sync` — exit 0; проверка наличия:

    sync exit=0
    19:    "pyside6>=6.11.2",
    23

Checkpoint:

    checkpoint exit=0
    Qt 6.11.2

## Итог

Фаза 1 завершена: runtime-зависимость `pyside6` 6.11.2 добавлена через `uv add pyside6`,
`[dependency-groups] dev` не тронута, существующие зависимости сохранены.
Checkpoint зелёный (exit 0, `Qt 6.11.2`). Блокеров нет.