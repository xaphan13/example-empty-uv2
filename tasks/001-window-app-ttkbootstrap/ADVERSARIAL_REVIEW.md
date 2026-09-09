# Adversarial review — ex_window_app_ttkbootstrap

**Прогнано 13 атак, ожидаемо PASS — 12, находок — 1.**

Покрытие:
- Группа 1 (edge-case аргументы CLI): 1a–1j — 10 кейсов.
- Группа 2 (cwd-зависимость из /tmp): 2, 2b — 2 кейса (под uv `--project` cwd
  принудительно выставляется в проект — модуль находится; попытка обойти это
  через `PYTHONPATH` + `--no-project` упёрлась в нехватку `aiosqlite`, см. ниже).
- Группа 3 (реестр и раннер напрямую): 3a (идемпотентность, восстановление
  `print`/`logging`/`sys.stderr` после `run_example`), 3b (split stdout/stderr).
- Группа 4 (параллельность): два `--smoke` одновременно.
- Группа 5 (`--smoke-window 0.001` под Xvfb) + добивка `--smoke-window -1/0` под Xvfb.

Что НЕ атаковал (за рамками задания) и почему:
- Внутренности `ex_*` примеров: подменены для smoke-режима и
  проверены через `--smoke` — повторная атака на них вне зоны GUI-пакета.
- UI-разметка `.ui` (wigets, темы) — на это уже есть критерии 4–5,
  функционально проверено в qa.

Зависших процессов после прогона нет (`pgrep -af "main_window_app" — exit 1`).
`/tmp/log` от попытки 2b убран вручную сразу после обнаружения.

---

## ADV-001: --smoke-window с нечисловым значением даёт необработанный traceback
- Серьёзность: **low**
- Команда/шаги:
  ```bash
  uv run python -m ex_window_app_ttkbootstrap.main_window_app --smoke-window abc
  ```
- Фактическое поведение:
  ```
  exit=1
  Traceback (most recent call last):
    File "<frozen runpy>", line 198, in _run_module_as_main
    ...
    File ".../main_window_app.py", line 240, in main
      return _run_smoke_window(float(seconds))
  ValueError: could not convert string to float: 'abc'
  ```
- Ожидаемое (по спеке / здравому смыслу): argparse принимает любое
  позиционное значение, но в спеке фазы 4 `--smoke-window` объявлен
  как «SECONDS» (число). Пользовательский ввод `"abc"` — это
  однозначно ошибка пользователя; корректное поведение — чистое
  сообщение `argument --smoke-window: invalid float value: 'abc'`
  с exit=2 (как делает argparse при `type=float`), либо явный
  pre-parse-чек. Сейчас же argparse пропускает строку, и она падает
  в `float()` уже внутри `_run_smoke_window` с необработанным
  `ValueError` и traceback на stderr — для CLI это шумно и
  не соответствует стилю обработки остальных пользовательских
  ошибок в этом модуле (см. `_run_smoke` для `KeyError`).
- Disposition: ACCEPTED -> DEF-001 (исправлено backend-dev, qa перепроверил, DEF-001 CLOSED — 2026-09-08)
- Замечание: проявляется только без `xvfb-run` (до создания окна
  вообще не доходит). Под `xvfb-run` — падает позже с TclError
  по тем же причинам. Серьёзность low: это CLI-эргономика, не
  поломка функциональности (флаги с числовым значением работают
  корректно, в т.ч. `-1`, `0`, `0.001` — проверено ADV-005/006).

---

## Сводка по остальным атакам (PASS, без записи в находки)

| # | Атака | Команда | Результат |
|---|---|---|---|
| ADV-002 | `--smoke ""` (пустое имя) | `... --smoke ""` | exit=2, в stderr: `Unknown example id: ''. Known ids: ...` — корректно, как в `KeyError`-ветке `_run_smoke`. |
| ADV-003 | `--smoke --smoke-window 5` (взаимоисключающие флаги) | `... --smoke --smoke-window 5` | exit=2, в stderr: `Ошибка: --smoke и --smoke-window нельзя использовать одновременно.` — корректно по спеке. |
| ADV-004 | `--smoke valid_BRACKET` (неверный регистр) | `... --smoke valid_BRACKET` | exit=2, в stderr: `Unknown example id: 'valid_BRACKET'. Known ids: ...` — корректно, реестр чувствителен к регистру, что согласуется с `ExampleDescriptor.example_id`. |
| ADV-005 | `--smoke-window 0.001` под Xvfb | `xvfb-run -a uv run ... --smoke-window 0.001` | exit=0, ~1 сек. Окно успело подняться и закрыться. |
| ADV-006 | `--smoke-window -1` / `0` под Xvfb | `xvfb-run -a uv run ... --smoke-window -1` и `... --smoke-window 0` | оба exit=0. Защита `max(1, int(round(seconds * 1000)))` в `_run_smoke_window` корректно клампит к 1 мс. |
| ADV-007 | `--smoke valid_bracket --smoke-window 3` (оба сразу) | `... --smoke valid_bracket --smoke-window 3` | exit=2, та же mutual-exclusion ошибка. |
| ADV-008 | `--help` | `... --help` | exit=0, usage с описанием трёх режимов. |
| ADV-009 | `--smoke=valid_bracket` (через `=`) | `... --smoke=valid_bracket` | exit=0, корректный захваченный вывод с 3 строками `inn()` (две одинаковые — это исходный `valid_bracket.py:36-37` дважды вызывает `isValid('({[]})')`, **не дубликат раннера**). |
| ADV-010 | cwd-зависимость из `/tmp` | `cd /tmp && uv run --project /home/max/.../example-empty-uv2 python -m ex_window_app_ttkbootstrap.main_window_app --smoke valid_bracket` | exit=0. `uv run --project` принудительно ставит cwd в корень проекта, модуль находится. `ui_path` в `application_window.py` использует `Path(__file__).with_name(...)` (проверено grep'ом по коду), не зависит от cwd. |
| ADV-011 | Идемпотентность `run_example` и восстановление stdout/stderr/логгера | `python -c "from ex_window_app_ttkbootstrap.example_runner import run_example; ... out1 = run_example('valid_bracket'); out2 = run_example('valid_bracket'); print('MARKER_AFTER_ALL_RUNS')"` | exit=0. `len(out1) == len(out2) == 337` (детерминированный вывод). После `run_example`: `print` уходит в stdout, `sys.stderr.write` — в stderr, `logging.info` пишет на корневой логгер. Всё восстановлено. |
| ADV-012 | Параллельный `--smoke` двух примеров | `... --smoke valid_bracket & ... --smoke zip_operations & wait` | оба exit=0. Захваченный вывод в каждом корректный. Гонки за `log/empty-uv2.log` нет (строки от двух процессов перемежаются в файле — это особенность `ConfigLogger.RotatingFileHandler`, а не GUI-пакета; в каждом отдельном захваченном выводе строки целые). |
| ADV-013 | `pkill` после прогона | `pgrep -af "main_window_app\|python -m ex_window"` | exit=1 — никаких зависших процессов не осталось. |

---

## Потенциальные будущие находки (вне рамок этого задания, наблюдение)

- `ConfigLogger` (в `config_log.py:5`) использует `LOG_DIR = "./log"`. При запуске
  НЕ через `uv run --project` (т.е. если кто-то вызовет `python -m ...` напрямую
  из чужого cwd) `__create_log_dir` создаст `<cwd>/log/empty-uv2.log`. Под
  `uv run --project` uv сам выставляет cwd, поэтому проблема не проявляется;
  но если в будущем добавить запуск из произвольной директории (Docker-entrypoint,
  systemd unit) — `ConfigLogger` либо начнёт мусорить в cwd, либо упадёт
  (прав на запись нет). Это к самому GUI-пакету отношения не имеет, к
  заданию не относится, фиксирую как гипотезу.
