# DEFECTS — ex_window_app_pyside6 (оконный пример PySide6/Qt6)

Задание: `tasks/current/REQUIREMENTS.md`. Все проверки — локальные, headless
(`QT_QPA_PLATFORM=offscreen`), без сервера; cwd = корень проекта. Код продукта не
правился.

Шкала серьёзности: Major — нарушает требование задания; Minor — ухудшает; Cosmetic —
косметика.

---

## DEF-001 — `--smoke-window inf` даёт traceback и exit 1 вместо exit 2

- **Severity:** Major
- **Status:** CLOSED
- **Критерий REQUIREMENTS.md:** №7 «Некорректные аргументы дают exit 2 без traceback»
- **Found by:** adversary (ADV-001)
- **Adv-ссылка:** `tasks/current/ADVERSARIAL_REVIEW.md`, запись ADV-001
- **Доказательство:** `e2e/qa_adv_repro.md`, раздел «--smoke-window inf»

### Шаги воспроизведения

1. Из корня проекта запустить приложение в headless-режиме с нечисловым по смыслу,
   но проходящим `float()`, значением:
   ```bash
   QT_QPA_PLATFORM=offscreen timeout 20 uv run python -m ex_window_app_pyside6.main_window_app --smoke-window inf
   ```
2. Дождаться завершения процесса (значение должно быть отсеяно на этапе разбора
   аргументов, до создания окна).

### Ожидаемый результат

argparse отклоняет `inf` как некорректное значение `--smoke-window` → **exit 2**,
понятное сообщение в stderr, **без traceback**.

### Фактический результат

`inf` проходит валидацию `_positive_float` (проверка `seconds <= 0` для `inf` даёт
`False`), окно создаётся, и только затем падает `int(args.smoke_window * 1000)`:

```
File ".../ex_window_app_pyside6/main_window_app.py", line 111, in main
    QTimer.singleShot(int(args.smoke_window * 1000), app.quit)
OverflowError: cannot convert float infinity to integer
exit=1
```

Необработанный traceback, **exit 1** вместо ожидаемого exit 2.

### History

- 2026-09-10 — qa: воспроизведено по шагам выше, `exit=1`,
  `OverflowError: cannot convert float infinity to integer` (строка 111
  `main_window_ctk.py`). Сырой вывод — `e2e/qa_adv_repro.md`. Запись создана со
  статусом OPEN, исправление не проверялось.
- 2026-09-10 — backend-dev: ИСПРАВЛЕНО. В `_positive_float`
  (`../../ex_window_app_pyside6/main_window_pyside.py`) добавлен `import math` и условие
  `if not math.isfinite(seconds) or seconds <= 0:` вместо `if seconds <= 0:`.
  Прогон: `--smoke-window inf` → exit 2, stderr
  `argument --smoke-window: значение должно быть > 0: 'inf'`, traceback отсутствует;
  ruff чист. Сырой вывод — `dev/fix_def01_checkpoint.txt`, прогресс —
  `dev/fix_def01_progress.md`. Статус переведён в FIX-READY, перепроверка — за qa.
- 2026-09-10 — qa: перепроверено после фикса. `--smoke-window inf` → exit 2, stderr
  `argument --smoke-window: значение должно быть > 0: 'inf'`, traceback отсутствует.
  Регресс: `-1`/`abc` → exit 2, `--smoke` → `smoke ok` exit 0, `--smoke-window 3` →
  exit 0 за ~3,57 с; `uv run ruff check .` — без ошибок. Сырой вывод —
  `e2e/qa_def_recheck.md`. Статус переведён в CLOSED.

---

## DEF-002 — `--smoke-window nan` даёт traceback и exit 1 вместо exit 2

- **Severity:** Major
- **Status:** CLOSED
- **Критерий REQUIREMENTS.md:** №7 «Некорректные аргументы дают exit 2 без traceback»
- **Found by:** adversary (ADV-002)
- **Adv-ссылка:** `tasks/current/ADVERSARIAL_REVIEW.md`, запись ADV-002
- **Доказательство:** `e2e/qa_adv_repro.md`, раздел «--smoke-window nan»

### Шаги воспроизведения

1. Из корня проекта запустить приложение в headless-режиме:
   ```bash
   QT_QPA_PLATFORM=offscreen timeout 20 uv run python -m ex_window_app_pyside6.main_window_app --smoke-window nan
   ```
2. Дождаться завершения процесса.

### Ожидаемый результат

argparse отклоняет `nan` → **exit 2**, сообщение в stderr, **без traceback**.

### Фактический результат

`nan <= 0` даёт `False`, поэтому проверка «строго > 0» пропускает NaN; падение
происходит позже, на `int()`:

```
File ".../ex_window_app_pyside6/main_window_app.py", line 111, in main
    QTimer.singleShot(int(args.smoke_window * 1000), app.quit)
ValueError: cannot convert float NaN to integer
exit=1
```

Необработанный traceback, **exit 1** вместо ожидаемого exit 2.

### History

- 2026-09-10 — qa: воспроизведено по шагам выше, `exit=1`,
  `ValueError: cannot convert float NaN to integer` (строка 111
  `main_window_ctk.py`). Сырой вывод — `e2e/qa_adv_repro.md`. Запись создана со
  статусом OPEN, исправление не проверялось.
- 2026-09-10 — backend-dev: ИСПРАВЛЕНО. Тот же корень, что и DEF-001: добавлена
  проверка конечности `math.isfinite`. Прогон: `--smoke-window nan` → exit 2, stderr
  `argument --smoke-window: значение должно быть > 0: 'nan'`, traceback отсутствует.
  Сырой вывод — `dev/fix_def01_checkpoint.txt`. Статус переведён в FIX-READY,
  перепроверка — за qa.
- 2026-09-10 — qa: перепроверено после фикса. `--smoke-window nan` → exit 2, stderr
  `argument --smoke-window: значение должно быть > 0: 'nan'`, traceback отсутст��ует.
  Регресс и ruff зелёные — см. `e2e/qa_def_recheck.md`. Статус переведён в CLOSED.

---

## DEF-003 — `--smoke-window 1e309` (переполнение во float inf) даёт traceback и exit 1 вместо exit 2

- **Severity:** Major
- **Status:** CLOSED
- **Критерий REQUIREMENTS.md:** №7 «Некорректные аргументы дают exit 2 без traceback»
- **Found by:** adversary (ADV-003)
- **Adv-ссылка:** `tasks/current/ADVERSARIAL_REVIEW.md`, запись ADV-003
- **Доказательство:** `e2e/qa_adv_repro.md`, раздел «--smoke-window 1e309»

### Шаги воспроизведения

1. Из корня проекта запустить приложение в headless-режиме с числовой на вид, но
   переполняющейся записью:
   ```bash
   QT_QPA_PLATFORM=offscreen timeout 20 uv run python -m ex_window_app_pyside6.main_window_app --smoke-window 1e309
   ```
2. Дождаться завершения процесса.

### Ожидаемый результат

Значение отклоняется как некорректное → **exit 2**, сообщение в stderr, **без
traceback**.

### Фактический результат

`float("1e309")` переполняется в `inf`, далее тот же корень, что и в DEF-001:

```
File ".../ex_window_app_pyside6/main_window_app.py", line 111, in main
    QTimer.singleShot(int(args.smoke_window * 1000), app.quit)
OverflowError: cannot convert float infinity to integer
exit=1
```

Необработанный traceback, **exit 1** вместо ожидаемого exit 2. В отличие от DEF-001,
достижим обычной десятичной записью — без явных слов `inf`/`nan`.

### History

- 2026-09-10 — qa: воспроизведено по шагам выше, `exit=1`,
  `OverflowError: cannot convert float infinity to integer` (строка 111
  `main_window_ctk.py`). Сырой вывод — `e2e/qa_adv_repro.md`. Запись создана со
  статусом OPEN, исправление не проверялось.
- 2026-09-10 — backend-dev: ИСПРАВЛЕНО. Тот же корень, что и DEF-001: `1e309`
  переполняется в `inf`, теперь отсекается `math.isfinite`. Прогон:
  `--smoke-window 1e309` → exit 2, stderr
  `argument --smoke-window: значение должно быть > 0: '1e309'`, traceback
  отсутствует. Сырой вывод — `dev/fix_def01_checkpoint.txt`. Статус переведён в
  FIX-READY, перепроверка — за qa.
- 2026-09-10 — qa: перепроверено после фикса. `--smoke-window 1e309` → exit 2, stderr
  `argument --smoke-window: значение должно быть > 0: '1e309'`, traceback отсутствует.
  Регресс и ruff зелёные — см. `e2e/qa_def_recheck.md`. Статус переведён в CLOSED.

---

## Сводка

| ID | Аргумент | Severity | Status | ADV |
|---|---|---|---|---|
| DEF-001 | `--smoke-window inf` | Major | CLOSED | ADV-001 |
| DEF-002 | `--smoke-window nan` | Major | CLOSED | ADV-002 |
| DEF-003 | `--smoke-window 1e309` | Major | CLOSED | ADV-003 |

Общий корень: `_positive_float` проверяла только `seconds <= 0`, поэтому `inf` и `nan`
проходили валидацию и падали на `int(args.smoke_window * 1000)` в `main()`
(`main_window_ctk.py`, строка 111). Исправление: добавлена проверка
`not math.isfinite(seconds) or seconds <= 0`. Все три сценария перепроверены qa после
фикса — exit 2, traceback отсутствует, регресс и ruff зелёные
(`e2e/qa_def_recheck.md`); DEF-001..003 переведены в CLOSED.