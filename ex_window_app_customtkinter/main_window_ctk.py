"""Точка входа пакета `ex_window_app_customtkinter` и headless-smoke.

Модуль даёт три режима запуска:

1. Без аргументов — открыть окно `ApplicationWindow` и войти в Tk
   `mainloop()`. Это обычный пользовательский сценарий.

2. `--smoke [name]` — headless-проверка реестра примеров. Импортируется
   только `example_runner` (без `tkinter`/`customtkinter`/`pygubu`),
   вызывается `run_example(name)`, результат печатается в stdout,
   процесс завершается с кодом 0. Если `name` не указан — берётся
   первый пример из реестра (`list_examples()[0].example_id`). Если
   `name` неизвестно — в stderr выводится понятное сообщение и
   процесс завершается с кодом 2 (без traceback — для удобства qa).

3. `--smoke-window [sec]` — полный smoke под `xvfb-run`. Создаётся
   `ApplicationWindow`, через `window.after(sec * 1000, ...)` планируется
   закрытие окна, после чего `mainloop()` отрабатывает до выхода.
   По умолчанию — 5 секунд. Процесс завершается с кодом 0.

Импорт модуля не создаёт ни одного GUI-объекта: `ApplicationWindow`
импортируется лениво внутри `main()` и только в тех ветках, где он
действительно нужен. Это позволяет `python -c "import ex_window_app_customtkinter.main_window_app"`
работать без дисплея и без побочных эффектов (грабля из AGENTS.md).
"""

from __future__ import annotations

import argparse
import sys
from typing import Sequence


# ------------------------------------------------------------------------
# Константы
# ------------------------------------------------------------------------
# Код возврата для случая "неизвестное имя примера в --smoke".
# Любое ненулевое значение годится; выбрано 2, чтобы отличать от
# необработанного исключения (1) и от нормального exit 0.
_EXIT_UNKNOWN_EXAMPLE: int = 2

# Код возврата при ошибке пользователя в аргументах (argparse сам
# печатает usage и уходит с 2; здесь дублируем для ясности).
_EXIT_BAD_ARGS: int = 2

# Окно smoke-window по умолчанию (секунды). Подобрано так, чтобы
# окно успело подняться и отрисоваться, но прогон не висел долго.
_DEFAULT_SMOKE_WINDOW_SECONDS: float = 5.0


# ------------------------------------------------------------------------
# Парсинг аргументов
# ------------------------------------------------------------------------
def _positive_float(raw: str) -> float:
    """Argparse type-функция: парсит строку в float > 0.

    Требует СТРОГО положительное значение: ноль и отрицательные числа
    не имеют смысла для «задержки перед закрытием окна» и должны
    отсекаться argparse с понятным сообщением и exit=2 (а не
    молча превращаться в 1 мс через `max(1, ...)`, см. DEF-003).
    `float(raw)` сам поднимает `ValueError` при нечисловой строке —
    argparse превращает его в `ArgumentTypeError` с сообщением
    "invalid float value: '...'", что совпадает с нашим сообщением
    форматом.
    """
    try:
        value = float(raw)
    except ValueError:
        # Перевыбрасываем как `argparse.ArgumentTypeError` — argparse
        # печатает его с префиксом `error: argument --smoke-window:`
        # и завершает процесс с exit=2.
        raise argparse.ArgumentTypeError(
            f"invalid float value: {raw!r}"
        )
    if value <= 0:
        raise argparse.ArgumentTypeError(
            f"значение должно быть числом > 0 (получено {raw!r})"
        )
    return value


def _build_parser() -> argparse.ArgumentParser:
    """Сконструировать парсер аргументов CLI.

    Парсер держится отдельно от `main()`, чтобы его можно было
    вызвать повторно (например, из тестов) без побочных эффектов
    и без импорта GUI-модулей.
    """
    parser = argparse.ArgumentParser(
        prog="python -m ex_window_app_customtkinter.main_window_app",
        description=(
            "Запуск GUI-примера на CustomTkinter + pygubu. "
            "Без флагов открывает окно; --smoke запускает пример "
            "headless; --smoke-window поднимает окно под Xvfb и "
            "закрывает его автоматически."
        ),
    )
    # `--smoke [name]`: опциональное позиционное значение после флага.
    # `nargs="?"` — имя может отсутствовать; `default=None` —
    # маркер «имя явно не задано» (отличается от пустой строки).
    parser.add_argument(
        "--smoke",
        nargs="?",
        const=None,
        default=False,
        metavar="NAME",
        help=(
            "Headless-smoke: запустить пример NAME из реестра "
            "без создания окна и напечатать захваченный вывод. "
            "Без NAME — первый пример из реестра."
        ),
    )
    # `--smoke-window [sec]`: длительность прогона окна (секунды,
    # можно дробное). По умолчанию 5 секунд.
    # `type=float` валидирует значение на этапе argparse: при
    # нечисловом вводе ('abc', '5x') argparse сам печатает
    # `argument --smoke-window: invalid float value: 'abc'` в stderr
    # и завершает процесс с exit=2 (без traceback, без нашего
    # ValueError). Это закрывает DEF-001.
    # `default=False` НЕ проходит через `type=`: argparse вызывает
    # `type` только для значений, пришедших из argv или из `const`;
    # `default` подставляется в результат как есть. Поэтому
    # `args.smoke_window` остаётся либо `False` (флаг не передан),
    # либо `float` (флаг передан — со значением или без).
    parser.add_argument(
        "--smoke-window",
        nargs="?",
        # `type=_positive_float`: отсекает мусор (`abc`, `-5`, `0`)
        # с понятным сообщением и exit=2, закрывая DEF-003. До этого
        # `type=float` пропускал `-5` и `-5 * 1000 = -5000` зажимался
        # в `max(1, ...)` до 1 мс — окно поднималось и мгновенно
        # закрывалось без предупреждения.
        type=_positive_float,
        const=_DEFAULT_SMOKE_WINDOW_SECONDS,
        default=False,
        metavar="SECONDS",
        help=(
            "Поднять окно и закрыть его автоматически через SECONDS "
            "секунд (по умолчанию 5.0; должно быть > 0). "
            "Используется под xvfb-run."
        ),
    )
    return parser


# ------------------------------------------------------------------------
# Ветка --smoke (headless, без GUI)
# ------------------------------------------------------------------------
def _run_smoke(name: str | None) -> int:
    """Выполнить пример `name` (или первый из реестра) headless.

    Возвращает код возврата: 0 при успехе, 2 при неизвестном имени.

    Здесь намеренно НЕ импортируется `application_window` —
    только `example_runner`. Это даёт qa дешёвую проверку
    реестра и `run_example` без подъёма Tk.
    """
    # Импорт локально, чтобы ветка GUI не тащила runner в память
    # и наоборот. У `example_runner` нет побочных GUI-эффектов.
    from ex_window_app_customtkinter.example_runner import (
        list_examples,
        run_example,
    )

    if name is None:
        # `list_examples()` возвращает копию реестра, поэтому
        # `[0]` безопасно. Пустой реестр теоретически невозможен
        # (фаза 2 зафиксировала 5 дескрипторов), но защищаемся явно.
        examples = list_examples()
        if not examples:
            print(
                "Ошибка: реестр примеров пуст.",
                file=sys.stderr,
                flush=True,
            )
            return _EXIT_UNKNOWN_EXAMPLE
        name = examples[0].example_id

    try:
        output = run_example(name)
    except KeyError as exc:
        # `run_example` поднимает `KeyError` с подсказкой
        # (список известных id) при неизвестном имени. Печатаем
        # чистое сообщение, без traceback — это и есть контракт
        # чекпоинта фазы 4.
        print(str(exc), file=sys.stderr, flush=True)
        return _EXIT_UNKNOWN_EXAMPLE

    # `output` уже содержит \n между записями (см. `_format_record`
    # в `example_runner.py`). `print` добавит финальный перевод
    # строки, что удобно для интерактивного просмотра.
    print(output, flush=True)
    return 0


# ------------------------------------------------------------------------
# Ветка --smoke-window (полный smoke под Xvfb)
# ------------------------------------------------------------------------
def _run_smoke_window(seconds: float) -> int:
    """Создать окно, закрыть его через `seconds` секунд, выйти с 0.

    Закрытие планируется через `window.after(seconds * 1000, ...)` —
    это миллисекунды, поэтому `seconds` умножается на 1000.
    В обработчике закрытия (`ApplicationWindow._on_close`) вызывается
    `self.window.quit()`, который корректно завершает `mainloop`.
    `mainloop()` возвращает управление, и мы выходим с кодом 0.

    Дробное `seconds` поддерживается: `after` принимает int в
    большинстве версий Tk, поэтому округляем до целого. 1 мс
    точности на пятисекундном smoke избыточна.
    """
    # Импорт локально — см. соглашение в `_run_smoke`.
    from ex_window_app_customtkinter.application_window import ApplicationWindow

    app = ApplicationWindow()
    delay_ms = max(1, int(round(seconds * 1000)))
    # `_on_close` уже делает `self.window.quit()`. После `quit`
    # `mainloop` возвращает управление, и процесс завершается
    # штатно (daemon-поток воркера, если он был, тоже умрёт).
    app.window.after(delay_ms, app._on_close)
    app.window.mainloop()
    return 0


# ------------------------------------------------------------------------
# Обычный запуск (mainloop)
# ------------------------------------------------------------------------
def _run_gui() -> int:
    """Создать окно и войти в `mainloop()`. Возврат — из `mainloop`.

    После `mainloop()` (например, после клика по крестику) управление
    возвращается сюда, и мы выходим с кодом 0. Нештатные исключения
    из GUI-кода не маскируются — пусть падают с ненулевым кодом.
    """
    from ex_window_app_customtkinter.application_window import ApplicationWindow

    app = ApplicationWindow()
    app.window.mainloop()
    return 0


# ------------------------------------------------------------------------
# Точка входа
# ------------------------------------------------------------------------
def main(argv: Sequence[str] | None = None) -> int:
    """Разобрать argv и выполнить выбранный режим.

    `argv` — параметризовано для удобства тестирования: если
    передано `None`, используется `sys.argv[1:]` (стандартное
    поведение argparse). Возвращает код возврата процесса.
    """
    parser = _build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    # `--smoke` и `--smoke-window` — взаимоисключающие: одновременно
    # они не имеют смысла (smoke не открывает окно, smoke-window —
    # открывает и закрывает). argparse не разруливает это за нас,
    # делаем вручную с понятным сообщением.
    if args.smoke is not False and args.smoke_window is not False:
        print(
            "Ошибка: --smoke и --smoke-window нельзя использовать "
            "одновременно.",
            file=sys.stderr,
            flush=True,
        )
        return _EXIT_BAD_ARGS

    # Ветка 1: headless-smoke.
    if args.smoke is not False:
        # `args.smoke` — None, если флаг передан без значения;
        # строка — если значение передано; False — если флаг
        # не передан вообще. Этой логики достаточно для nargs="?".
        name = args.smoke if args.smoke is not False else None
        return _run_smoke(name)

    # Ветка 2: smoke-window (полный smoke под Xvfb).
    if args.smoke_window is not False:
        # Внешний `is not False` уже гарантирует, что флаг передан.
        # `type=float` в парсере означает, что `args.smoke_window`
        # — это либо `float` (const подставлен при `nargs="?"` без
        # значения, либо пользовательское значение прошло через
        # `float()`), либо `False` (default, но эту ветку мы уже
        # отсекли выше). Дополнительное `float()` и явная защита
        # от `False` не нужны — это и есть упрощение после фикса
        # DEF-001.
        seconds: float = args.smoke_window
        return _run_smoke_window(seconds)

    # Ветка 3: обычный запуск GUI.
    return _run_gui()


if __name__ == "__main__":
    # `sys.exit` с int-передачей — стандартный способ вернуть
    # код возврата из `python -m ...`. Любое необработанное
    # исключение приведёт к exit 1 и traceback — это и есть
    # нужное поведение для диагностики.
    raise SystemExit(main())
