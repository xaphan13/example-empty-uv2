"""Оконный класс `ApplicationWindow` для пакета `ex_window_app_ttkbootstrap`.

Назначение:
- загрузить разметку из `window_app.ui` через `pygubu.Builder`;
- встроить её в `ttkbootstrap.Window` с тёмной темой по умолчанию;
- связать виджеты по stable id (см. фазу 2) с обработчиками;
- запускать курируемые примеры из `example_runner.run_example` в
  фоновом потоке, доставляя вывод в `output_text` через `queue.Queue`
  и `window.after(...)` (обязательно из главного потока Tk).

Импорт модуля безопасен для headless-сред:
никакие GUI-объекты (`Tk`, `ttkbootstrap.Window`, загрузка `.ui`)
не создаются на уровне модуля — только при вызове `ApplicationWindow(...)`.
"""

from __future__ import annotations

import logging
import queue
import threading
import tkinter as tk
import traceback
from collections.abc import Callable
from pathlib import Path
from typing import Final

import pygubu
import ttkbootstrap

from ex_window_app_ttkbootstrap.example_runner import (
    ExampleDescriptor,
    list_examples,
    run_example,
)


# ------------------------------------------------------------------------
# Константы
# ------------------------------------------------------------------------
# Только тёмные темы ttkbootstrap (см. REQUIREMENTS.md, раздел
# "Подтверждённые решения"). Порядок в кортеже — это порядок в
# выпадающем списке окна.
_DARK_THEMES: Final[tuple[str, ...]] = (
    "darkly",
    "superhero",
    "cyborg",
    "solar",
    "vapor",
)
_DEFAULT_THEME: Final[str] = "darkly"

# Интервал опроса очереди из главного потока (мс). 100 мс — баланс
# между отзывчивостью UI и нагрузкой на event loop.
_QUEUE_POLL_MS: Final[int] = 100

# Тексты статусов — единая точка правды, чтобы qa/adversary могли
# проверять состояние окна по строке.
_STATUS_READY: Final[str] = "Готово"
_STATUS_RUNNING: Final[str] = "Выполняется..."
_STATUS_DONE: Final[str] = "Завершено"
_STATUS_ERROR: Final[str] = "Ошибка"

# Имя .ui-файла лежит рядом с этим модулем. Путь разрешается через
# `Path(__file__).with_name(...)`, чтобы не зависеть от cwd — см.
# "cwd-зависимость" в AGENTS.md.
_UI_FILENAME: Final[str] = "window_app.ui"


# ------------------------------------------------------------------------
# ApplicationWindow
# ------------------------------------------------------------------------
class ApplicationWindow:
    """Главное окно GUI-примера: виджеты + запуск курируемых примеров.

    Жизненный цикл:
    1. `__init__` поднимает `ttkbootstrap.Window`, загружает `.ui`,
       привязывает виджеты и подключает обработчики.
    2. Вызывающий код (`main_window_app.py` в фазе 4) стартует
       `self.window.mainloop()`.
    3. Внутри `mainloop` пользователь выбирает пример/тему, жмёт
       "Запустить" — `_start_example` запускает `threading.Thread`,
       который зовёт `run_example(name)`. Результат или traceback
       попадают в `self._queue`.
    4. Главный поток через `self.window.after(_QUEUE_POLL_MS, self._poll_queue)`
       забирает сообщения из очереди и обновляет виджеты.

    Все мутации `output_text` и `status_label` происходят только из
    главного потока — внутри `_poll_queue`, который вызывается из
    `after()`. Воркер только кладёт данные в очередь.

    Импорт модуля не создаёт ни одного GUI-объекта: ни `Tk`, ни
    `ttkbootstrap.Window`, ни `Builder` — поэтому `python -c
    "from ex_window_app_ttkbootstrap.application_window import
    ApplicationWindow"` работает без дисплея.
    """

    def __init__(self) -> None:
        # Путь к .ui разрешаем от файла модуля, а не от cwd — иначе
        # запуск из другой директории уронит Builder (`FileNotFoundError`).
        ui_path = Path(__file__).with_name(_UI_FILENAME)

        # Сначала окно, потом builder. `Window` создаёт `Tk()` внутри
        # себя; это допустимо, потому что мы уже в `__init__`, а не
        # на уровне модуля. Тема по умолчанию — `darkly` (см. _DEFAULT_THEME).
        self.window = ttkbootstrap.Window(
            title="ttkbootstrap + pygubu — запуск примеров",
            themename=_DEFAULT_THEME,
        )

        builder = pygubu.Builder()
        builder.add_from_file(str(ui_path))
        self.main_frame = builder.get_object("main_frame", self.window)
        self.main_frame.pack(fill="both", expand=True)

        # ---- Привязка виджетов по stable id (контракт фазы 2) ----
        # Все id зафиксированы в `window_app.ui`. Если какой-то id
        # переименуют в .ui, `builder.get_object` поднимет KeyError —
        # это правильный fail-fast на стадии разработки.
        self.example_combobox: ttkbootstrap.Combobox = builder.get_object(
            "example_combobox", self.window
        )
        self.theme_combobox: ttkbootstrap.Combobox = builder.get_object(
            "theme_combobox", self.window
        )
        self.filter_entry: ttkbootstrap.Entry = builder.get_object(
            "filter_entry", self.window
        )
        self.run_button: ttkbootstrap.Button = builder.get_object(
            "run_button", self.window
        )
        self.clear_button: ttkbootstrap.Button = builder.get_object(
            "clear_button", self.window
        )
        self.output_text: tk.Text = builder.get_object(
            "output_text", self.window
        )
        self.progressbar: ttkbootstrap.Progressbar = builder.get_object(
            "progressbar", self.window
        )
        self.status_label: ttkbootstrap.Label = builder.get_object(
            "status_label", self.window
        )
        # Скроллбар — необязательный по контракту id, но без него
        # длинный вывод будет недоступен. Связываем его с `output_text`.
        try:
            output_scroll: ttkbootstrap.Scrollbar = builder.get_object(
                "output_scroll", self.window
            )
            output_scroll.config(command=self.output_text.yview)
            self.output_text.config(yscrollcommand=output_scroll.set)
        except KeyError:
            # Скроллбар в .ui не описан — это терпимо: text wrap="word"
            # в любом случае не даёт уходить вправо, и Tk по умолчанию
            # показывает системный скроллбар при переполнении.
            output_scroll = None  # noqa: F841 — оставлено для отладки

        # ---- Реестр примеров: маппинг title ↔ id ----
        # В combobox показываем `title` (человекочитаемо), а запускаем
        # по `id` (стабильный ключ реестра). Двухсторонние словари —
        # чтобы фильтр и перерисовка списка могли искать по любой стороне.
        examples: list[ExampleDescriptor] = list_examples()
        self._title_to_id: dict[str, str] = {
            descriptor.title: descriptor.example_id for descriptor in examples
        }
        self._id_to_title: dict[str, str] = {
            descriptor.example_id: descriptor.title for descriptor in examples
        }
        # Полный список на текущий момент — фильтр работает на нём.
        self._all_titles: list[str] = [descriptor.title for descriptor in examples]

        # ---- Наполнение комбобоксов ----
        # `example_combobox` — список заголовков; `theme_combobox` —
        # список тёмных тем. Оба в режиме `readonly` (задан в .ui).
        self.example_combobox.configure(values=self._all_titles)
        if self._all_titles:
            self.example_combobox.set(self._all_titles[0])

        self.theme_combobox.configure(values=list(_DARK_THEMES))
        self.theme_combobox.set(_DEFAULT_THEME)

        # ---- Очередь и состояние воркера ----
        # Очередь между фоновым потоком и главным потоком Tk. Поток
        # кладёт кортежи: (kind, payload), где kind ∈ {"done", "error"}.
        self._queue: queue.Queue[tuple[str, object]] = queue.Queue()
        # Активный поток-исполнитель примера (None, если ничего не идёт).
        self._worker: threading.Thread | None = None

        # ---- Стартовое состояние ----
        # `progressbar` в indeterminate-режиме не двигается без `start()`;
        # явный `stop()` при инициализации — страховка от визуального
        # "застрявшего" заполнения, если .ui когда-нибудь поменяют.
        self.progressbar.stop()
        self._set_status(_STATUS_READY)
        self._set_running(False)

        # ---- Подключение обработчиков ----
        # `<<ComboboxSelected>>` срабатывает и на клик, и на
        # программный `.set()` — для смены темы это нормально:
        # при инициализации `theme_combobox.set(_DEFAULT_THEME)` тоже
        # триггерит событие, но `theme_use(_DEFAULT_THEME)` идемпотентен.
        self.theme_combobox.bind(
            "<<ComboboxSelected>>", self._on_theme_selected
        )
        # Фильтр — через StringVar.trace_add: ловим любое изменение
        # `filter_entry`, включая программное `set()`.
        self._filter_var = tk.StringVar()
        self.filter_entry.configure(textvariable=self._filter_var)
        self._filter_var.trace_add("write", self._on_filter_changed)

        self.run_button.configure(command=self._on_run_clicked)
        self.clear_button.configure(command=self._on_clear_clicked)

        # Закрытие окна крестиком — чисто завершаем mainloop, не
        # оставляя висящих потоков (daemon-потоки и так умрут вместе
        # с процессом, но явный `quit` корректнее для qa/adversary).
        self.window.protocol("WM_DELETE_WINDOW", self._on_close)

    # ----------------------------------------------------------------
    # Управление состоянием UI
    # ----------------------------------------------------------------
    def _set_status(self, text: str) -> None:
        """Установить текст статусной строки. Вызывать из главного потока."""
        self.status_label.configure(text=text)

    def _set_running(self, running: bool) -> None:
        """Переключить блокировку UI на время выполнения примера.

        Блокируем кнопку запуска (чтобы не запустить пример повторно,
        пока старый поток ещё не вернул результат), а также combobox'ы
        и поле фильтра — иначе пользователь может поменять выбор
        посреди выполнения и ожидать, что новый пример запустится
        следующим.
        """
        if running:
            self.run_button.configure(state="disabled")
            self.example_combobox.configure(state="disabled")
            self.theme_combobox.configure(state="disabled")
            self.filter_entry.configure(state="disabled")
        else:
            self.run_button.configure(state="normal")
            self.example_combobox.configure(state="readonly")
            self.theme_combobox.configure(state="readonly")
            self.filter_entry.configure(state="normal")

    def _append_output(self, text: str) -> None:
        """Дописать текст в конец `output_text`. Только из главного потока.

        В конце — автопрокрутка к последней строке, чтобы пользователь
        видел свежий вывод без ручного скролла.
        """
        self.output_text.configure(state="normal")
        self.output_text.insert("end", text)
        # `end-1c` — на символ перед финальным \n, чтобы курсор
        # оказался на последнем видимом символе, а не под ним.
        self.output_text.see("end-1c")

    def _clear_output(self) -> None:
        """Очистить `output_text`. Только из главного потока."""
        self.output_text.configure(state="normal")
        self.output_text.delete("1.0", "end")

    # ----------------------------------------------------------------
    # Фильтрация example_combobox
    # ----------------------------------------------------------------
    def _on_filter_changed(self, *_args: object) -> None:
        """Обработчик изменения `filter_entry`: фильтрует список примеров.

        Фильтрация по подстроке, case-insensitive. Текущий выбор
        сохраняется, если он остался в новом списке; иначе —
        выбирается первая подходящая запись (или пустая строка).
        """
        query = self._filter_var.get().strip().lower()
        if query:
            filtered = [
                title for title in self._all_titles if query in title.lower()
            ]
        else:
            filtered = list(self._all_titles)

        self.example_combobox.configure(values=filtered)

        previous_title = self.example_combobox.get()
        if previous_title in filtered:
            # Текущий выбор всё ещё в списке — оставляем.
            self.example_combobox.set(previous_title)
        elif filtered:
            # Выбор пропал из фильтра — ставим первую подходящую.
            self.example_combobox.set(filtered[0])
        else:
            # Ничего не подошло — чистим выбор, чтобы запуск не
            # стартовал с устаревшим id.
            self.example_combobox.set("")

    # ----------------------------------------------------------------
    # Смена темы
    # ----------------------------------------------------------------
    def _on_theme_selected(self, _event: object) -> None:
        """Применить выбранную тему к ttkbootstrap-стилю.

        Используем `ttkbootstrap.Style().theme_use(...)` — это
        рекомендованный путь смены темы на лету; виджеты перерисуются
        автоматически.
        """
        theme = self.theme_combobox.get()
        if not theme:
            return
        ttkbootstrap.Style().theme_use(theme)

    # ----------------------------------------------------------------
    # Запуск примера в потоке
    # ----------------------------------------------------------------
    def _selected_example_id(self) -> str | None:
        """Вернуть `example_id` по текущему выбору в `example_combobox`.

        `None`, если выбор пуст или такого title больше нет в реестре
        (теоретически невозможно, потому что combobox наполняется из
        реестра, но защищаемся явно).
        """
        title = self.example_combobox.get()
        if not title:
            return None
        return self._title_to_id.get(title)

    def _on_run_clicked(self) -> None:
        """Кнопка "Запустить": проверить выбор и стартовать воркер."""
        if self._worker is not None:
            # Дублирующий клик, пока воркер жив. `_set_running(False)`
            # при предыдущем завершении уже разблокировал кнопку,
            # так что в норме сюда не попадаем — но это дешёвая защита
            # от гонки между `after` и кликом.
            return

        example_id = self._selected_example_id()
        if example_id is None:
            self._set_status(_STATUS_ERROR)
            self._append_output("Не выбран пример для запуска.\n")
            return

        self._start_example(example_id)

    def _start_example(self, example_id: str) -> None:
        """Подготовить UI и запустить пример `example_id` в потоке.

        1. Проверить, что воркера нет (идемпотентность).
        2. Заблокировать UI, очистить `output_text`, выставить статус.
        3. Запустить `progressbar.start(...)` — `indeterminate` крутит
           «бегущий» индикатор; передаём `_QUEUE_POLL_MS`, чтобы шаг
           анимации совпадал с интервалом опроса.
        4. Создать daemon-поток и положить его в `self._worker`.
        5. Запланировать `_poll_queue` через `self.window.after`.
        """
        if self._worker is not None:
            return

        # Блокируем UI до возврата воркера.
        self._set_running(True)
        self._clear_output()
        title = self._id_to_title.get(example_id, example_id)
        self._append_output(f"=== Запуск: {title} ({example_id}) ===\n")
        self._set_status(_STATUS_RUNNING)
        self.progressbar.start(_QUEUE_POLL_MS)

        # Daemon-поток: при завершении процесса поток не помешает
        # выходу; при обычной работе его состояние держим в `self._worker`
        # и якорим из главного потока.
        self._worker = threading.Thread(
            target=self._run_in_worker,
            args=(example_id,),
            name=f"example-runner-{example_id}",
            daemon=True,
        )
        self._worker.start()

        # `after` из главного потока Tk. Возвращаемое значение
        # (id таймера) нам не нужно: `cancel` не предусмотрен —
        # `_poll_queue` сам перестаёт планировать себя, когда
        # воркер завершился и очередь пуста.
        self.window.after(_QUEUE_POLL_MS, self._poll_queue)

    def _run_in_worker(self, example_id: str) -> None:
        """Тело фонового потока: вызвать `run_example` и положить результат.

        `run_example` пробрасывает исключения примера дальше. Оборачиваем
        вызов `try/except`, чтобы окно не падало, а traceback попал
        в `output_text` как обычный вывод. В очередь кладём кортеж
        `(kind, payload)`: kind — `"done"` (с готовой строкой) или
        `"error"` (с traceback).
        """
        try:
            result = run_example(example_id)
        except Exception:
            # `traceback.format_exc()` уже включает финальный `\n`,
            # отдельный суффикс не нужен.
            self._queue.put(("error", traceback.format_exc()))
            return
        self._queue.put(("done", result))

    def _poll_queue(self) -> None:
        """Главный поток: забрать из очереди и обновить UI.

        Поведение:
        - Пока воркер жив или в очереди что-то лежит — забираем
          `get_nowait`, обрабатываем каждое сообщение.
        - Когда получаем терминальное сообщение (`done`/`error`):
          останавливаем `progressbar`, разблокируем UI, обновляем
          `status_label`, сбрасываем `self._worker = None`.
        - Если воркер уже завершился и очередь пуста — на этом
          опрос заканчивается (новых `after` не планируем).
        - В любом другом случае (воркер жив, очередь пуста) —
          планируем следующий опрос.
        """
        terminal: tuple[str, object] | None = None
        try:
            while True:
                kind, payload = self._queue.get_nowait()
                if kind == "done":
                    # `payload` — многострочная строка; добавляем как есть.
                    self._append_output(str(payload))
                    terminal = (kind, payload)
                elif kind == "error":
                    self._append_output(f"[ОШИБКА]\n{payload}\n")
                    terminal = (kind, payload)
                else:
                    # Неизвестный kind — логируем и считаем терминалом,
                    # чтобы окно не «зависло» в режиме выполнения.
                    logging.getLogger(__name__).warning(
                        "Unknown queue message kind: %r", kind
                    )
                    terminal = (kind, payload)
        except queue.Empty:
            pass

        if terminal is not None:
            # Терминальное сообщение — закрываем прогон.
            self.progressbar.stop()
            self._set_running(False)
            kind, _payload = terminal
            if kind == "done":
                self._set_status(_STATUS_DONE)
            else:
                self._set_status(_STATUS_ERROR)
            self._worker = None
            return

        # Нетерминальный опрос: воркер ещё работает либо только что
        # завершился, но сообщение ещё не дошло. Планируем следующий
        # тик, пока воркер жив, и один «дожим» после завершения, чтобы
        # забрать финальное сообщение. Это безопаснее, чем одно
        # условие: даже если воркер умер между `get_nowait` и `after`,
        # `_poll_queue` сам себя остановит терминальной веткой выше.
        if self._worker is not None or not self._queue.empty():
            self.window.after(_QUEUE_POLL_MS, self._poll_queue)
        else:
            # Ни воркера, ни сообщений — но терминала мы не получили.
            # Достижимо только при сбое протокола (например, поток упал
            # до `put`) или при ручном `_poll_queue` вне `mainloop`.
            # В реальном `mainloop` этот путь не достигается: после
            # терминального сообщения `_poll_queue` не планирует
            # следующий тик. Чистим только прогресс и блокировку UI,
            # статус не трогаем — если воркер успел выставить
            # «Ошибка» или «Завершено» через терминальную ветку,
            # мы его не перетираем.
            self.progressbar.stop()
            self._set_running(False)

    # ----------------------------------------------------------------
    # Очистка вывода и закрытие
    # ----------------------------------------------------------------
    def _on_clear_clicked(self) -> None:
        """Кнопка "Очистить": стереть `output_text` и сбросить статус."""
        self._clear_output()
        self._set_status(_STATUS_READY)

    def _on_close(self) -> None:
        """Обработчик закрытия окна (крестик): корректно выйти из mainloop.

        `self._worker` — daemon-поток; при выходе из процесса он и так
        умрёт. Явный `quit` нужен, чтобы `mainloop` вернул управление
        вызывающему коду, а не оставил окно «висеть» в фоне.
        """
        self.window.quit()
