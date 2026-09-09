"""Пакет ex_window_app_ttkbootstrap — GUI-пример на ttkbootstrap + pygubu.

Содержит:
- example_runner.py — реестр курируемых примеров и запуск с захватом вывода.
- application_window.py — класс окна (фаза 3).
- main_window_app.py — точка входа и headless-smoke (фаза 4).
- window_app.ui — XML-разметка Pygubu (фаза 2).

Пакет намеренно не импортирует GUI-модули на уровне модуля, чтобы
импорт был дешёвым и безопасным для headless-проверок.
"""
