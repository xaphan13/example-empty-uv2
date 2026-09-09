"""Программный сценарий для проверки DEF-001: запуск примера через GUI.

Создаёт ApplicationWindow, программно выбирает карточку valid_bracket,
кликает «Запустить», дожидается результата и печатает состояние UI.
Запускать под Xvfb :99.
"""

import sys
import traceback

import customtkinter as ctk  # noqa: F401

from ex_window_app_customtkinter.application_window import ApplicationWindow


results: dict[str, object] = {}


def step1(app: ApplicationWindow) -> None:
    """Выбрать карточку и кликнуть «Запустить»."""
    try:
        app._on_card_click("valid_bracket")
        app._on_run_clicked()
        results["step1_ok"] = True
    except Exception:
        results["step1_ok"] = False
        results["step1_tb"] = traceback.format_exc()


def step2(app: ApplicationWindow) -> None:
    """Проверить состояние UI после прогона."""
    try:
        txt = app.output_text.get("1.0", "end")
        results["output_len"] = len(txt)
        results["output_first200"] = txt[:200]
        results["has_launch_header"] = "=== Запуск:" in txt
        results["has_result"] = ("res = " in txt) or ("True" in txt)
        results["status"] = str(app.status_label.cget("text"))
        results["metric_status"] = str(
            app.metric_status_value.cget("text")
        )
        results["sidebar_w"] = app.sidebar_frame.winfo_width()
        results["content_w"] = app.content_frame.winfo_width()
        results["worker_alive"] = (
            app._worker is not None and app._worker.is_alive()
        )
    except Exception:
        results["step2_tb"] = traceback.format_exc()
    finally:
        try:
            app.window.destroy()
        except Exception:
            pass


def main() -> int:
    app = ApplicationWindow()
    app.window.update_idletasks()
    # Сначала форсируем отрисовку под Xvfb (один тик mainloop), затем
    # планируем шаги. between-кадровые задержки дают Tk время
    # обработать after/poll_queue.
    app.window.after(500, lambda: step1(app))
    app.window.after(3500, lambda: step2(app))
    # Запасной «kill switch» — если что-то залипло, mainloop отпустит
    # через 6 секунд.
    app.window.after(6000, app.window.quit)
    app.window.mainloop()

    print("step1_ok:", results.get("step1_ok"))
    if "step1_tb" in results:
        print("step1_tb:", results["step1_tb"])
    print("output_len:", results.get("output_len"))
    print("output_first200:", repr(results.get("output_first200")))
    print("has_launch_header:", results.get("has_launch_header"))
    print("has_result:", results.get("has_result"))
    print("status:", repr(results.get("status")))
    print("metric_status:", repr(results.get("metric_status")))
    print("sidebar_w:", results.get("sidebar_w"))
    print("content_w:", results.get("content_w"))
    print("worker_alive:", results.get("worker_alive"))
    if "step2_tb" in results:
        print("step2_tb:", results["step2_tb"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
