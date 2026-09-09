"""Программный сценарий adversary: поднять окно, кликать виджеты, проверить.

Запускается через `DISPLAY=:99 timeout 60 uv run python dev/adv_programmatic_test.py`.
Не оставляет за собой процессов — все вызовы синхронны, окно
закрывается через `window.after(...)` в конце.
"""
from __future__ import annotations

import json
import sys
import traceback


def _out(payload: dict) -> None:
    """Печатать JSON-строку в stdout (стабильный для парсинга)."""
    print("ADV_JSON " + json.dumps(payload, ensure_ascii=False), flush=True)


def main() -> int:
    from ex_window_app_customtkinter.application_window import ApplicationWindow

    results: list[dict] = []
    app = ApplicationWindow()

    # ---- 1. Стартовое состояние ----
    try:
        results.append({
            "name": "startup",
            "output_text_empty": not bool(
                app.output_text.get("1.0", "end-1c").strip()
            ),
            "run_text": app.run_button.cget("text"),
            "status": app.status_label.cget("text"),
            "metric_registry": app.metric_registry_value.cget("text"),
            "metric_status": app.metric_status_value.cget("text"),
            "metric_last_run": app.metric_last_run_value.cget("text"),
            "search_counter": app.search_counter.cget("text"),
            "example_title": app.example_title.cget("text"),
            "selected": app._selected_example_id,
            "total": app._total_examples,
            "card_ids": list(app._cards.keys()),
        })
    except Exception as exc:
        results.append({"name": "startup", "error": repr(exc)})

    # ---- 2. Запуск без выбора карточки ----
    try:
        # До любого клика по карточке
        before_status = app.status_label.cget("text")
        app._on_run_clicked()
        app.window.update_idletasks()
        after_status = app.status_label.cget("text")
        results.append({
            "name": "run_no_selection",
            "before_status": before_status,
            "after_status": after_status,
            "output_unchanged": not bool(
                app.output_text.get("1.0", "end-1c").strip()
            ),
        })
    except Exception as exc:
        results.append({
            "name": "run_no_selection",
            "error": repr(exc),
            "tb": traceback.format_exc(),
        })

    # ---- 3. Программный выбор карточки (вызов handler без event) ----
    try:
        app._on_card_click("valid_bracket")
        app.window.update_idletasks()
        results.append({
            "name": "select_card",
            "selected": app._selected_example_id,
            "status": app.status_label.cget("text"),
            "example_title": app.example_title.cget("text"),
        })
    except Exception as exc:
        results.append({
            "name": "select_card",
            "error": repr(exc),
            "tb": traceback.format_exc(),
        })

    # ---- 4. Фильтр поиска, под который ничего не подходит ----
    try:
        before_counter = app.search_counter.cget("text")
        app._search_var.set("qqqzzz_no_match")
        app.window.update_idletasks()
        after_counter = app.search_counter.cget("text")
        # Видимость карточек: проверяем winfo_viewable
        viewable = {
            eid: bool(app._cards[eid].winfo_viewable())
            for eid in app._cards
        }
        results.append({
            "name": "search_no_match",
            "before_counter": before_counter,
            "after_counter": after_counter,
            "viewable": viewable,
        })
    except Exception as exc:
        results.append({
            "name": "search_no_match",
            "error": repr(exc),
            "tb": traceback.format_exc(),
        })

    # ---- 5. Очистка поиска и клик «Копировать» при пустом выводе ----
    try:
        app._search_var.set("")
        app.window.update_idletasks()
        # Вывод должен быть пустым после очистки + предыдущей очистки перед run_no_selection
        empty_output = not bool(app.output_text.get("1.0", "end-1c").strip())
        app._on_copy_clicked()
        app.window.update_idletasks()
        copy_status = app.status_label.cget("text")
        results.append({
            "name": "copy_empty",
            "empty_output": empty_output,
            "status": copy_status,
        })
    except Exception as exc:
        results.append({
            "name": "copy_empty",
            "error": repr(exc),
            "tb": traceback.format_exc(),
        })

    # ---- 6. Кнопка «Очистить» — не падает ----
    try:
        app._append_output("тестовый мусор\n")
        app._on_clear_clicked()
        app.window.update_idletasks()
        cleared = not bool(app.output_text.get("1.0", "end-1c").strip())
        results.append({
            "name": "clear",
            "cleared": cleared,
            "status": app.status_label.cget("text"),
        })
    except Exception as exc:
        results.append({
            "name": "clear",
            "error": repr(exc),
            "tb": traceback.format_exc(),
        })

    # ---- 7. Запуск примера через run_button (sync-ожидание) ----
    try:
        # Сначала выберем снова
        app._on_card_click("valid_bracket")
        # Запустим и подождём
        app._on_run_clicked()
        # Подождём до завершения воркера (макс 15 с)
        import time
        start = time.monotonic()
        while app._worker is not None and time.monotonic() - start < 15:
            app.window.update()
            app._poll_queue()
            time.sleep(0.05)
        results.append({
            "name": "run_valid_bracket",
            "duration_s": round(time.monotonic() - start, 3),
            "final_status": app.status_label.cget("text"),
            "metric_status": app.metric_status_value.cget("text"),
            "metric_last_run": app.metric_last_run_value.cget("text"),
            "output_len": len(app.output_text.get("1.0", "end-1c")),
            "output_has_bracket": "valid" in app.output_text.get("1.0", "end-1c").lower(),
        })
    except Exception as exc:
        results.append({
            "name": "run_valid_bracket",
            "error": repr(exc),
            "tb": traceback.format_exc(),
        })

    # ---- 8. Двойной invoke run_button подряд ----
    try:
        app._on_card_click("zip_operations")
        # Первый клик — стартует воркер
        app._on_run_clicked()
        # Сразу второй — должен игнорироваться защитой
        app._on_run_clicked()
        import time
        start = time.monotonic()
        while app._worker is not None and time.monotonic() - start < 15:
            app.window.update()
            app._poll_queue()
            time.sleep(0.05)
        results.append({
            "name": "double_run",
            "final_status": app.status_label.cget("text"),
            "output_len": len(app.output_text.get("1.0", "end-1c")),
        })
    except Exception as exc:
        results.append({
            "name": "double_run",
            "error": repr(exc),
            "tb": traceback.format_exc(),
        })

    # ---- 9. Свитчи: переключение clear_before_run, потом запуск ----
    try:
        # Сначала очистим и проверим, что после запуска вывод чист
        app._on_clear_clicked()
        # Выключим clear_before_run
        app.clear_before_run_switch.deselect()
        app._on_card_click("metaclass_vars")
        # Добавим мусор в вывод — при выключенном clear должно остаться
        app._append_output("Мусор до запуска\n")
        app._on_run_clicked()
        import time
        start = time.monotonic()
        while app._worker is not None and time.monotonic() - start < 15:
            app.window.update()
            app._poll_queue()
            time.sleep(0.05)
        output = app.output_text.get("1.0", "end-1c")
        results.append({
            "name": "switch_clear_off",
            "cleared_before_run_preserved_musor": "Мусор до запуска" in output,
            "output_len": len(output),
            "output_has_metaclass": "FUNC" in output,
        })
    except Exception as exc:
        results.append({
            "name": "switch_clear_off",
            "error": repr(exc),
            "tb": traceback.format_exc(),
        })

    # ---- 10. Размер окна и проверка геометрии ----
    try:
        app.window.update_idletasks()
        results.append({
            "name": "geometry",
            "winfo_width": app.window.winfo_width(),
            "winfo_height": app.window.winfo_height(),
            "main_width": app.main_frame.winfo_width(),
            "sidebar_width": app.sidebar_frame.winfo_width(),
            "content_width": app.content_frame.winfo_width(),
        })
    except Exception as exc:
        results.append({
            "name": "geometry",
            "error": repr(exc),
        })

    # ---- Закрытие ----
    for r in results:
        _out(r)
    app._on_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
