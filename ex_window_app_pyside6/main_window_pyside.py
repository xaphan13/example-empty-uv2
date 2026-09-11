"""Точка входа примера на PySide6: три режима запуска.

Режимы:
- обычный запуск (без флагов) — окно показывается, работает ``app.exec()``;
- ``--smoke`` — окно конструируется, виджеты проверяются по objectName,
  печатается ``smoke ok``, окно не показывается (``show()`` не вызывается);
- ``--smoke-window [SECONDS]`` — окно показывается и закрывается через указанное
  число секунд (по умолчанию 5.0).

``QApplication`` создаётся только внутри ``main()``; на уровне модуля
GUI-объектов нет, импорт модуля окно не открывает.
"""

from __future__ import annotations

import argparse
import math
import sys
from collections.abc import Sequence

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

from ex_window_app_pyside6.application_window import ApplicationWindow

# Ожидаемые objectName виджетов — контракт фазы 2, на него опирается --smoke.
EXPECTED_OBJECT_NAMES = (
    "application_window",
    "name_input",
    "message_input",
    "show_button",
    "clear_button",
    "result_label",
    "volume_slider",
    "slider_value_label",
    "mode_checkbox",
    "theme_combo",
    "progress_bar",
)


def _positive_float(value: str) -> float:
    """Разбирает аргумент как строго положительное число секунд.

    При неверном значении argparse завершает работу с кодом 2 и сообщением в stderr.
    """
    try:
        seconds = float(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"не число: {value!r}") from exc
    if not math.isfinite(seconds) or seconds <= 0:
        raise argparse.ArgumentTypeError(f"значение должно быть > 0: {value!r}")
    return seconds


def _build_parser() -> argparse.ArgumentParser:
    """Собирает парсер аргументов командной строки с тремя режимами."""
    parser = argparse.ArgumentParser(
        prog="python -m ex_window_app_pyside6.main_window_app",
        description="Пример окна на PySide6: обычный запуск, --smoke, --smoke-window.",
    )
    parser.add_argument(
        "--smoke",
        action="store_true",
        help="собрать окно, проверить виджеты по objectName и напечатать 'smoke ok'",
    )
    parser.add_argument(
        "--smoke-window",
        nargs="?",
        type=_positive_float,
        const=5.0,
        default=False,
        metavar="SECONDS",
        help="показать окно и закрыть его через SECONDS секунд (по умолчанию 5.0)",
    )
    return parser


def _run_smoke() -> int:
    """Собирает окно без показа и проверяет наличие виджетов по objectName."""
    window = ApplicationWindow()
    present = {
        window.objectName(),
        window.name_input.objectName(),
        window.message_input.objectName(),
        window.show_button.objectName(),
        window.clear_button.objectName(),
        window.result_label.objectName(),
        window.volume_slider.objectName(),
        window.slider_value_label.objectName(),
        window.mode_checkbox.objectName(),
        window.theme_combo.objectName(),
        window.progress_bar.objectName(),
    }
    missing = [name for name in EXPECTED_OBJECT_NAMES if name not in present]
    if missing:
        print(f"smoke failed: отсутствуют виджеты {missing}", file=sys.stderr)
        return 1
    print("smoke ok")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    """Запускает пример в одном из трёх режимов и возвращает код возврата."""
    parser = _build_parser()
    args = parser.parse_args(argv)

    # Одновременная передача флагов недопустима: сообщение в stderr и код 2.
    if args.smoke and args.smoke_window is not False:
        print("Нельзя одновременно использовать --smoke и --smoke-window", file=sys.stderr)
        return 2

    app = QApplication([])

    if args.smoke:
        return _run_smoke()

    window = ApplicationWindow()
    window.show()

    if args.smoke_window is not False:
        QTimer.singleShot(int(args.smoke_window * 1000), app.quit)

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())