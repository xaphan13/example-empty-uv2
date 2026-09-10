# QA: воспроизведение ADV-001..003 (некорректные --smoke-window)

Дата: 2026-09-10T20:21:09+03:00

## --smoke-window inf
$ QT_QPA_PLATFORM=offscreen timeout 20 uv run python -m ex_window_app_pyside6.main_window_app --smoke-window inf
This plugin does not support propagateSizeHints()
Traceback (most recent call last):
  File "<frozen runpy>", line 198, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "/home/max/0_0_26_new_one/example-empty-uv2/ex_window_app_pyside6/main_window_app.py", line 117, in <module>
    raise SystemExit(main())
                     ^^^^^^
  File "/home/max/0_0_26_new_one/example-empty-uv2/ex_window_app_pyside6/main_window_app.py", line 111, in main
    QTimer.singleShot(int(args.smoke_window * 1000), app.quit)
                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
OverflowError: cannot convert float infinity to integer
exit=1

## --smoke-window nan
$ QT_QPA_PLATFORM=offscreen timeout 20 uv run python -m ex_window_app_pyside6.main_window_app --smoke-window nan
This plugin does not support propagateSizeHints()
Traceback (most recent call last):
  File "<frozen runpy>", line 198, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "/home/max/0_0_26_new_one/example-empty-uv2/ex_window_app_pyside6/main_window_app.py", line 117, in <module>
    raise SystemExit(main())
                     ^^^^^^
  File "/home/max/0_0_26_new_one/example-empty-uv2/ex_window_app_pyside6/main_window_app.py", line 111, in main
    QTimer.singleShot(int(args.smoke_window * 1000), app.quit)
                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
ValueError: cannot convert float NaN to integer
exit=1

## --smoke-window 1e309
$ QT_QPA_PLATFORM=offscreen timeout 20 uv run python -m ex_window_app_pyside6.main_window_app --smoke-window 1e309
This plugin does not support propagateSizeHints()
Traceback (most recent call last):
  File "<frozen runpy>", line 198, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "/home/max/0_0_26_new_one/example-empty-uv2/ex_window_app_pyside6/main_window_app.py", line 117, in <module>
    raise SystemExit(main())
                     ^^^^^^
  File "/home/max/0_0_26_new_one/example-empty-uv2/ex_window_app_pyside6/main_window_app.py", line 111, in main
    QTimer.singleShot(int(args.smoke_window * 1000), app.quit)
                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
OverflowError: cannot convert float infinity to integer
exit=1

