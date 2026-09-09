"""QA functional check for DEF-001/DEF-002: click card, run, verify, geometry.

Этот скрипт НЕ редактирует продукт. Запускать под Xvfb: `xvfb-run -a uv run python
tasks/current/dev/qa_def_check.py [mode]`, где mode = "def001" (default) или "def002_geom".

def001:
    - select valid_bracket
    - click "Запустить"
    - wait for completion
    - check: no TypeError, output_len > 100, has_launch_header, has_result,
      status = "Завершено", sidebar_w == 280

def002_geom:
    - set window 1400x900 -> check sidebar_w
    - set window 800x520  -> check sidebar_w AND content_w
    - both should be 280; content should shrink visibly
"""

from __future__ import annotations

import sys
import traceback


def _import_app():
    from ex_window_app_customtkinter.application_window import ApplicationWindow

    return ApplicationWindow


def run_def001() -> int:
    ApplicationWindow = _import_app()
    results: dict[str, object] = {}

    def step1(app) -> None:  # type: ignore[no-untyped-def]
        try:
            app._on_card_click("valid_bracket")
            app._on_run_clicked()
            results["step1_ok"] = True
        except Exception:
            results["step1_ok"] = False
            results["step1_tb"] = traceback.format_exc()

    def step2(app) -> None:  # type: ignore[no-untyped-def]
        try:
            txt = app.output_text.get("1.0", "end")
            results["output_len"] = len(txt)
            results["output_first200"] = txt[:200]
            results["output_last200"] = txt[-200:]
            results["has_launch_header"] = "=== Запуск:" in txt
            results["has_result"] = "res = " in txt and "True" in txt
            results["status"] = str(app.status_label.cget("text"))
            try:
                results["metric_status"] = str(app.metric_status_value.cget("text"))
            except Exception:
                results["metric_status"] = "<n/a>"
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

    app = ApplicationWindow()
    app.window.update_idletasks()
    app.window.after(500, lambda: step1(app))
    app.window.after(4000, lambda: step2(app))
    app.window.after(6000, app.window.quit)
    app.window.mainloop()

    print("=== DEF-001 functional check ===")
    print("step1_ok:", results.get("step1_ok"))
    if "step1_tb" in results:
        print("step1_tb:", results["step1_tb"])
    print("output_len:", results.get("output_len"))
    print("output_first200:", repr(results.get("output_first200")))
    print("output_last200:", repr(results.get("output_last200")))
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


def run_def002_geom() -> int:
    ApplicationWindow = _import_app()
    results: dict[str, object] = {}

    def check(app) -> None:  # type: ignore[no-untyped-def]
        try:
            # Big window
            app.window.geometry("1400x900")
            app.window.update_idletasks()
            results["big_sidebar_w"] = app.sidebar_frame.winfo_width()
            results["big_content_w"] = app.content_frame.winfo_width()
            results["big_window_w"] = app.window.winfo_width()
            results["big_window_h"] = app.window.winfo_height()

            # Small window
            app.window.geometry("800x520")
            app.window.update_idletasks()
            results["min_sidebar_w"] = app.sidebar_frame.winfo_width()
            results["min_content_w"] = app.content_frame.winfo_width()
            results["min_window_w"] = app.window.winfo_width()
            results["min_window_h"] = app.window.winfo_height()
        except Exception:
            results["check_tb"] = traceback.format_exc()
        finally:
            try:
                app.window.destroy()
            except Exception:
                pass

    app = ApplicationWindow()
    app.window.update_idletasks()
    app.window.after(1500, lambda: check(app))
    app.window.after(4000, app.window.quit)
    app.window.mainloop()

    print("=== DEF-002 geometry check ===")
    print("big_window:", results.get("big_window_w"), "x", results.get("big_window_h"))
    print("big_sidebar_w:", results.get("big_sidebar_w"))
    print("big_content_w:", results.get("big_content_w"))
    print("min_window:", results.get("min_window_w"), "x", results.get("min_window_h"))
    print("min_sidebar_w:", results.get("min_sidebar_w"))
    print("min_content_w:", results.get("min_content_w"))
    if "check_tb" in results:
        print("check_tb:", results["check_tb"])
    return 0


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "def001"
    if mode == "def001":
        sys.exit(run_def001())
    elif mode == "def002_geom":
        sys.exit(run_def002_geom())
    else:
        print(f"unknown mode: {mode}", file=sys.stderr)
        sys.exit(2)
