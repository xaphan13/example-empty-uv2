# Фаза 4: Точка входа и headless-smoke — прогресс

Дата: 2026-09-08
Сессия: backend-dev
Задание: `ex_window_app_ttkbootstrap/main_window_app.py` — точка входа
с `--smoke [name]` и `--smoke-window [sec]`.

## План (выполнен)

1. Создать прогресс-файл.
2. Одним `write_file` создать `main_window_ctk.py`:
   - На уровне модуля — только `import argparse`, `import sys`,
     `from typing import Sequence`, константы и декларации функций.
     `tkinter`/`ttkbootstrap`/`pygubu` НЕ импортируются.
   - `argparse.ArgumentParser` с двумя взаимоисключающими флагами:
     `--smoke [NAME]` (nargs="?", const=None, default=False) и
     `--smoke-window [SECONDS]` (nargs="?", const=5.0, default=False).
   - `_run_smoke(name)` — локально импортирует `example_runner`,
     поднимает первый пример, если `name is None`; ловит `KeyError`
     от `run_example` и печатает чистое сообщение в stderr, exit 2.
   - `_run_smoke_window(seconds)` — локально импортирует
     `ApplicationWindow`, планирует `app._on_close` через
     `app.window.after(int(round(seconds*1000)), ...)`, затем
     `app.window.mainloop()`. Закрытие из `_on_close` (`quit()`)
     корректно завершает mainloop.
   - `_run_gui()` — без флагов: `ApplicationWindow()` + `mainloop()`.
   - `main(argv=None)` — разбирает argv и роутит в одну из веток;
     `--smoke` + `--smoke-window` одновременно → ошибка в stderr, exit 2.
   - `if __name__ == "__main__": raise SystemExit(main())` —
     для запуска как `python -m ex_window_app_ttkbootstrap.main_window_app`.

## Сырые выводы checkpoint

### 1) ruff
```
$ uv run ruff check ex_window_app_ttkbootstrap/
All checks passed!
exit=0
```
Файл: `phase04_ruff.txt`.

### 2) --smoke valid_bracket
```
$ uv run python -m ex_window_app_ttkbootstrap.main_window_app --smoke valid_bracket
2026-09-08 23:38:38 [INFO] OnlyFile: '****' main_code_war - 'start'
2026-09-08 23:38:38 [INFO] OnlyFile: '****' run_valid - 'start'
2026-09-08 23:38:38 [INFO] OnlyFile: inn() - res = (True, '({[]})')
2026-09-08 23:38:38 [INFO] OnlyFile: inn() - res = (True, '({[]})')
2026-09-08 23:38:38 [INFO] OnlyFile: inn() - res = (False, '[', '(')
exit=0
```
5 строк лог-записей `isValid` (формат `inn() - res = (True, '({[]})')`).
Файл: `phase04_smoke_valid_bracket.txt`.

### 3) --smoke (без имени)
```
$ uv run python -m ex_window_app_ttkbootstrap.main_window_app --smoke
2026-09-08 23:38:39 [INFO] OnlyFile: '****' run_simple_demo - 'start'
2026-09-08 23:38:39 [WARNING] OnlyFile: MAIN ->'copy_context' : cont_var = val-1
2026-09-08 23:38:39 [WARNING] OnlyFile: MAIN ->'copy_context' : cont_var = val-4
2026-09-08 23:38:39 [INFO] OnlyFile: task-2: cont_var= val-2
2026-09-08 23:38:39 [INFO] OnlyFile: task-3: cont_var= val-3
2026-09-08 23:38:39 [WARNING] OnlyFile: task-2 ->'copy_context' : cont_var = set in task-2
2026-09-08 23:38:39 [WARNING] OnlyFile: task-3 ->'copy_context' : cont_var = set in task-3
2026-09-08 23:38:39 [WARNING] OnlyFile: MAIN ->'copy_context' : cont_var = val-4
exit=0
```
Поднялся первый пример реестра — `async_context_var` (видны `task-2/task-3`).
Файл: `phase04_smoke_noname.txt`.

### 4) --smoke nonexistent_name
```
$ uv run python -m ex_window_app_ttkbootstrap.main_window_app --smoke nonexistent_name
"Unknown example id: 'nonexistent_name'. Known ids: async_context_var, metaclass_vars, multiprocessing_demo, valid_bracket, zip_operations"
exit=2
```
Сообщение уходит в stderr, stdout пуст (проверено отдельным редиректом
`1>/tmp/out.txt 2>/tmp/err.txt`; см. `phase04_smoke_unknown.txt`).
Чистое сообщение без traceback, exit=2. Файл: `phase04_smoke_unknown.txt`.

### 5) --smoke-window 5 (под Xvfb)
```
$ time xvfb-run -a uv run python -m ex_window_app_ttkbootstrap.main_window_app --smoke-window 5
exit=0 elapsed=7s
```
Окно открылось под Xvfb, `after(5000, _on_close)` отработал,
`mainloop` завершился через `quit()`, процесс вышел с кодом 0
через ~7 секунд (5 с на окно + ~2 с на подъём Xvfb и Python).
В выводе нет ни одной строки, кроме пустого stdout/stderr.
Файл: `phase04_smoke_window.txt`.

### 6) Доп. проверка: headless-импорт модуля
```
$ uv run python -c "import ex_window_app_ttkbootstrap.main_window_app as m; print('import ok, has main:', hasattr(m, 'main'))"
import ok, has main: True
exit=0
```
Импорт не поднимает `Tk`/`Window`/`.ui` — `ApplicationWindow`
импортируется только внутри `_run_smoke_window` / `_run_gui`,
а `_run_smoke` импортирует только `example_runner`.

## Замечания по контракту

- Контракт явно говорит: «argparse с `--smoke` принимает
  необязательный позиционный аргумент (nargs="?", default=None);
  `--smoke-window` — тоже nargs="?" с default 5 (float или int)».
  В реализации использована идиома `nargs="?"` + `const=DEFAULT`
  + `default=False`, потому что:
    - `nargs="?"` сохраняет «значение или пусто»;
    - `const` подставляется, когда флаг передан без значения;
    - `default=False` отделяет «флаг передан» от «флаг не передан»
      (это маркер, а не реальное значение — argparse с nargs="?"
      без отдельного `default` трактует оба случая одинаково и
      отличить «--smoke» от «без флага» снаружи уже нельзя).
  Поведение для пользователя идентично: `--smoke valid_bracket`
  → `name='valid_bracket'`; `--smoke` → `name=None` (первый из реестра);
  без флага → обычный запуск.
- При проверке первого прогона через `tee 2>&1` я сначала решил,
  что `exit=0` для `nonexistent_name` — дефект. На деле `tee`
  маскировал код пайпа: реальный `exit=2` (подтверждено отдельным
  редиректом 1>/tmp/out 2>/tmp/err). Сообщение уходит в stderr,
  stdout пуст, как и должен.
- `--smoke-window` с дробным `seconds` поддерживается: `after`
  получает `int(round(seconds * 1000))`, минимум 1 мс (страховка
  от нуля/отрицательных значений).
- `_on_close` уже делает `self.window.quit()` — после
  `mainloop()` процесс завершается штатно. Никаких `destroy()`
  не требуется.
- Взаимоисключение `--smoke` и `--smoke-window` обработано вручную
  с понятным сообщением в stderr и exit=2 (argparse по умолчанию
  не разруливает конфликты флагов).

## Итог
Статус фазы: **ЗЕЛЁНЫЙ**.
- Файл `ex_window_app_ttkbootstrap/main_window_app.py` создан одним
  `write_file` (без правок существующих файлов).
- ruff чист по всему пакету.
- Все 4 checkpoint-команды из спецификации дают ожидаемый результат:
  smoke-именованный — вывод про скобки, exit 0; smoke-без-имени —
  первый пример (`async_context_var`), exit 0; smoke-неизвестное-имя —
  чистое сообщение в stderr, exit 2; smoke-window — exit 0 за ~7 с
  без traceback.
- Импорт модуля не поднимает GUI — дополнительный инвариант
  проверен отдельной командой.
- Никакие другие файлы не тронуты. Git не коммитился.

---

## Фикс DEF-001

Дата: 2026-09-08
Сессия: backend-dev
Задание: закрыть DEF-001 в `ex_window_app_ttkbootstrap/main_window_app.py`.
Суть: argparse-уровневая валидация `--smoke-window` через `type=float` плюс
упрощение мёртвой ветки в `main()`.

### Что изменено (только `main_window_ctk.py`)

1. В `_build_parser()` к `--smoke-window` добавлен `type=float`.
   Argparse теперь сам валидирует значение: при `'abc'` / `'5x'` печатает
   `argument --smoke-window: invalid float value: 'abc'` в stderr и уходит
   с exit=2 — без traceback, без нашего `ValueError`.
   `default=False` остался как маркер «флаг не передан»: `default` не
   проходит через `type=`-функцию, поэтому False-маркер не превращается
   в 0.0; `const=_DEFAULT_SMOKE_WINDOW_SECONDS` тоже сохранён и теперь
   проходит через `float` и остаётся `5.0` (round-trip без потерь).

2. В `main()` убрана мёртвая ветка:
   ```python
   if seconds is False:
       seconds = _DEFAULT_SMOKE_WINDOW_SECONDS
   ```
   Внешнее `if args.smoke_window is not False` уже отсекает случай, когда
   `seconds` равен False; `nargs="?"` + `const=DEFAULT` гарантируют, что
   при переданном флаге `args.smoke_window` — это float (5.0 из const
   или пользовательское значение, прогнанное через `float()`). Дополнительная
   защита и `float(seconds)` стали мёртвым кодом — удалены.

3. Вокруг `seconds: float = args.smoke_window` добавлен короткий русский
   комментарий, объясняющий, почему дополнительные приведения/проверки
   больше не нужны.

Других файлов не трогал. Git не коммитил (папка `ex_window_app_ttkbootstrap/`
и так под `??` — не отслеживается).

### Сырые выводы checkpoint

#### 1) ruff
```
$ uv run ruff check ex_window_app_ttkbootstrap/
All checks passed!
exit=0
```

#### 2) --smoke-window abc
```
$ uv run python -m ex_window_app_ttkbootstrap.main_window_app --smoke-window abc; echo "exit=$?"
exit=2
usage: python -m ex_window_app_ttkbootstrap.main_window_app
       [-h] [--smoke [NAME]] [--smoke-window [SECONDS]]
python -m ex_window_app_ttkbootstrap.main_window_app: error: argument --smoke-window: invalid float value: 'abc'
```
Чистое сообщение argparse, exit=2, БЕЗ traceback. Былшее `ValueError: could not
convert string to float: 'abc'` из `float(seconds)` больше не возникает.

#### 3) --smoke-window 5x
```
$ uv run python -m ex_window_app_ttkbootstrap.main_window_app --smoke-window 5x; echo "exit=$?"
exit=2
usage: python -m ex_window_app_ttkbootstrap.main_window_app
       [-h] [--smoke [NAME]] [--smoke-window [SECONDS]]
python -m ex_window_app_ttkbootstrap.main_window_app: error: argument --smoke-window: invalid float value: '5x'
```
Аналогично abc — exit=2, без traceback.

#### 4) --smoke-window 2 (под Xvfb)
```
$ xvfb-run -a uv run python -m ex_window_app_ttkbootstrap.main_window_app --smoke-window 2; echo "exit=$?"
exit=0
```
Окно поднялось, `after(2000, _on_close)` отработал, `mainloop` завершился
через `quit()`. stdout/stderr пусты, exit=0.

#### 5) --smoke-window 0.001 (под Xvfb)
```
$ xvfb-run -a uv run python -m ex_window_app_ttkbootstrap.main_window_app --smoke-window 0.001; echo "exit=$?"
exit=0
```
0.001 с проходит через `float()` нормально, клампится `max(1, 1) = 1` мс
(`int(round(0.001 * 1000))` = 0 → `max(1, ...)` = 1), окно открылось
и закрылось мгновенно, exit=0.

#### 6) --smoke valid_bracket (регресс)
```
$ uv run python -m ex_window_app_ttkbootstrap.main_window_app --smoke valid_bracket | tail -2; echo "exit=${PIPESTATUS[0]}"
2026-09-08 23:51:52 [INFO] OnlyFile: inn() - res = (False, '[', '(')

exit=0
```
`--smoke` не задет — работает как раньше, exit=0.

#### 7) --smoke valid_bracket --smoke-window 3 (взаимоисключение)
```
$ uv run python -m ex_window_app_ttkbootstrap.main_window_app --smoke valid_bracket --smoke-window 3; echo "exit=$?"
exit=2
Ошибка: --smoke и --smoke-window нельзя использовать одновременно.
```
Прежнее ручное сообщение о взаимоисключении, exit=2. Парсинг обоих флагов
прошёл штатно.

#### 8) --smoke-window -1 (под Xvfb, дополнительная проверка)
```
$ xvfb-run -a uv run python -m ex_window_app_ttkbootstrap.main_window_app --smoke-window -1; echo "exit=$?"
exit=0
```
Argparse трактует `-1` как значение флага (не как новый флаг — у нас
`nargs="?"` и `type=float`), `float('-1') = -1.0`, в `_run_smoke_window`
`max(1, int(round(-1 * 1000))) = max(1, -1000) = 1` мс, окно поднимается
и закрывается. exit=0. Поведение «-1 клампится к 1 мс, exit=0» сохранено.

### Замечание по `git status`

`ex_window_app_ttkbootstrap/` целиком под `??` в `git status` (не отслеживается
гитом — добавлено в предыдущей фазе 4, но не коммитилось), поэтому
`git diff --stat -- ex_window_app_ttkbootstrap/` показывает пусто. Сам файл
правлен — это видно по содержимому (строки 100, 245) и по результатам
checkpoint-команд. Коммитить не просили — оставил как есть.

### Итог фикса

- DEF-001 закрыт на уровне argparse: `abc`/`5x` дают чистое сообщение
  `invalid float value: '...'` и exit=2, без traceback.
- Мёртвый код в `main()` убран, поведение остальных кейсов не изменилось.
- ruff чист.
- Регресс по `--smoke`, взаимоисключению и отрицательным значениям —
  все ожидания сошлись.
- Других файлов не трогал, не коммитил.
