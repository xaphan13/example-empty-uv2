"""Оконный класс `ApplicationWindow` для пакета `ex_window_app_customtkinter`.

Назначение:
- загрузить разметку из `window_app.ui` через `pygubu.Builder`;
- встроить её в `customtkinter.CTk` с тёмной темой «blue»;
- связать виджеты по stable id (фаза 3, расширенные в фазе 7) с
  обработчиками;
- запускать курируемые примеры из `example_runner.run_example` в
  фоновом потоке, доставляя вывод в `output_text` через `queue.Queue`
  и `window.after(...)` (обязательно из главного потока Tk).

Импорт модуля безопасен для headless-сред:
никакие GUI-объекты (`Tk`, `CTk`, загрузка `.ui`) не создаются
на уровне модуля — только при вызове `ApplicationWindow(...)`.
"""

from __future__ import annotations

import customtkinter as ctk
import datetime as _dt
import pygubu
import queue
import threading
import tkinter as tk
import traceback
from pathlib import Path
from typing import Final

from ex_window_app_customtkinter.example_runner import (
    ExampleDescriptor,
    list_examples,
    run_example,
)


# ------------------------------------------------------------------------
# Константы
# ------------------------------------------------------------------------
# Тема CustomTkinter — статично тёмная, см. REQUIREMENTS.md раздел
# «Подтверждённые решения». Переключатель тем ttkbootstrap ушёл.
_APPEARANCE_MODE: Final[str] = "Dark"
_COLOR_THEME: Final[str] = "blue"

# Заголовок и геометрия окна (редизайн v2: 900x600, minsize 800x520).
_WINDOW_TITLE: Final[str] = "CustomTkinter — запуск примеров"
_WINDOW_GEOMETRY: Final[str] = "900x600"
_WINDOW_MINSIZE: Final[tuple[int, int]] = (800, 520)

# Палитра Tokyo Night — единая точка правды, чтобы grep по ключевым
# цветам в `application_window.py`/`window_app.ui` оставался зелёным.
# Все цвета соответствуют разделу «Цветовая палитра» дизайн-спеки.
_COLOR_ACCENT: Final[str] = "#7aa2f7"
_COLOR_ACCENT_HOVER: Final[str] = "#89b4fa"
_COLOR_CARD_FG: Final[str] = "#292e42"
_COLOR_CARD_BORDER: Final[str] = "#3b4261"
_COLOR_CARD_HOVER: Final[str] = "#363e59"
_COLOR_CARD_SELECTED_FG: Final[str] = "#2f334d"
_COLOR_CARD_SELECTED_BORDER: Final[str] = "#7aa2f7"
_COLOR_TEXT_PRIMARY: Final[str] = "#c0caf5"
_COLOR_TEXT_BRIGHT: Final[str] = "#e8ecfd"
_COLOR_TEXT_SECONDARY: Final[str] = "#565f89"
_COLOR_METRIC_REGISTRY: Final[str] = "#7dcfff"
_COLOR_METRIC_LAST_RUN: Final[str] = "#9ece6a"
_COLOR_METRIC_STATUS: Final[str] = "#c0caf5"
_COLOR_METRIC_ERROR: Final[str] = "#f7768e"
_COLOR_STATUS_DEFAULT: Final[str] = "#565f89"

# Интервал опроса очереди из главного потока (мс). 100 мс — баланс
# между отзывчивостью UI и нагрузкой на event loop.
_QUEUE_POLL_MS: Final[int] = 100

# Тексты статусов — единая точка правды, чтобы qa/adversary могли
# проверять состояние окна по строке.
_STATUS_READY: Final[str] = "Готово"
_STATUS_RUNNING: Final[str] = "Выполняется..."
_STATUS_DONE: Final[str] = "Завершено"
_STATUS_ERROR: Final[str] = "Ошибка"
_STATUS_NO_SELECTION: Final[str] = "Сначала выберите пример"
_STATUS_COPIED: Final[str] = "Вывод скопирован"
_STATUS_COPIED_EMPTY: Final[str] = "Нечего копировать"

# Тексты кнопок и метрик по умолчанию.
_BUTTON_RUN_TEXT: Final[str] = "Запустить"
_BUTTON_RUN_RUNNING: Final[str] = "Выполняется..."
_BUTTON_CLEAR_TEXT: Final[str] = "Очистить"
_BUTTON_COPY_TEXT: Final[str] = "Копировать"

_METRIC_REGISTRY_INITIAL: Final[str] = "5"
_METRIC_LAST_RUN_INITIAL: Final[str] = "—"
_METRIC_STATUS_INITIAL: Final[str] = "Готово"
_SEARCH_COUNTER_ALL: Final[str] = "Найдено: 5 из 5"

# Имя .ui-файла лежит рядом с этим модулем. Путь разрешается через
# `Path(__file__).with_name(...)`, чтобы не зависеть от cwd — см.
# «cwd-зависимость» в AGENTS.md.
_UI_FILENAME: Final[str] = "window_app.ui"

# Краткие описания для шапки (`example_desc`) — отдельная от подписи
# карточки формулировка, чтобы в шапке был связный текст «что делает
# пример», а в карточке — только маркер. Источник истины — здесь.
_EXAMPLE_DESCRIPTIONS: Final[dict[str, str]] = {
    "async_context_var": (
        "Демонстрация изоляции ContextVar между asyncio-задачами: "
        "значение, заданное в одной задаче, не «просачивается» в другую."
    ),
    "valid_bracket": (
        "Алгоритмическая задача: проверить баланс трёх видов скобок "
        "()[]{} во входной строке. Использует стек."
    ),
    "zip_operations": (
        "Работа с zip-архивами: создание, добавление файлов и "
        "чтение содержимого через модуль zipfile."
    ),
    "metaclass_vars": (
        "Метакласс, который перехватывает обращения к атрибутам "
        "через __getattribute__: иллюстрация неожиданных эффектов."
    ),
    "multiprocessing_demo": (
        "Сравнение Process, Pool и Executor: разветвлённые процессы "
        "и пулы воркеров, обмен данными через очереди."
    ),
}


# ------------------------------------------------------------------------
# ApplicationWindow
# ------------------------------------------------------------------------
class ApplicationWindow:
    """Главное окно GUI-примера: виджеты + запуск курируемых примеров.

    Жизненный цикл:
    1. `__init__` поднимает `ctk.CTk`, загружает `.ui`, привязывает
       виджеты и подключает обработчики; настраивает grid-веса
       (фаза 7, редизайн v2) — сайдбар фикс. ширина, контент
       растягивается, `output_text` и `cards_scroll` забирают всё
       свободное место.
    2. Вызывающий код (`main_window_app.py`) стартует
       `self.window.mainloop()`.
    3. Внутри `mainloop` пользователь выбирает пример кликом по
       карточке, жмёт «Запустить» — `_start_example` запускает
       `threading.Thread`, который зовёт `run_example(example_id)`.
       Готовая строка (или traceback) попадает в `self._queue`.
    4. Главный поток через
       `self.window.after(_QUEUE_POLL_MS, self._poll_queue)`
       забирает сообщения из очереди и обновляет виджеты.

    Все мутации виджетов происходят только из главного потока —
    внутри `_poll_queue`, который вызывается из `after()`. Воркер
    только кладёт данные в очередь.

    Импорт модуля не создаёт ни одного GUI-объекта: ни `Tk`, ни
    `ctk.CTk`, ни `Builder` — поэтому
    `python -c "from ex_window_app_customtkinter.application_window import
    ApplicationWindow"` работает без дисплея.
    """

    def __init__(self) -> None:
        # Путь к .ui разрешаем от файла модуля, а не от cwd — иначе
        # запуск из другой директории уронит Builder (`FileNotFoundError`).
        ui_path = Path(__file__).with_name(_UI_FILENAME)

        # Тема — до создания окна, чтобы дефолтные цвета CTk-виджетов
        # (не переопределённые в .ui явно) сразу встали в «blue».
        ctk.set_appearance_mode(_APPEARANCE_MODE)
        ctk.set_default_color_theme(_COLOR_THEME)

        # `ctk.CTk()` создаёт `Tk()` внутри себя; это допустимо,
        # потому что мы уже в `__init__`, а не на уровне модуля.
        self.window = ctk.CTk()
        self.window.title(_WINDOW_TITLE)
        self.window.geometry(_WINDOW_GEOMETRY)
        self.window.minsize(*_WINDOW_MINSIZE)

        # Pygubu-билдер. Плагин `pygubu.plugins.customtkinter`
        # подключается автоматически при импорте `pygubu`, поэтому
        # классы `customtkinter.*` в .ui резолвятся без явной
        # регистрации (проверено в `__init__.py` пакета `pygubu`).
        self.builder = pygubu.Builder()
        self.builder.add_from_file(str(ui_path))

        # Корневой `main_frame` (CTkFrame в .ui) встраивается прямо
        # в окно. Так в одном дереве виджетов — и CTk, и CTkFrame.
        self.main_frame = self.builder.get_object("main_frame", self.window)
        self.main_frame.pack(fill="both", expand=True)

        # ---- Grid-веса (контракт фазы 7) ----
        # Задаются кодом, потому что надёжнее layout'а из .ui:
        # pygubu иногда округляет веса до int, а здесь нам нужно
        # именно 0/1 (только две колонки, одна — растягиваемая).
        # main_frame: столбец 0 — сайдбар (weight 0, minsize рассчитан
        # так, чтобы при `padx=12` в `sidebar.grid_configure(...)`
        # ниже ячейка grid отдала sidebar'у ровно 280 px видимой
        # ширины: 280 (целевая ширина виджета) + 12 + 12 (padx
        # симметрично) = 304. Без явного minsize grid сжимает колонку
        # по содержимому (~233 px), см. DEF-002. Столбец 1 — контент
        # (weight 1, растягивается). Строка 0 растягивается.
        self.main_frame.columnconfigure(0, weight=0, minsize=304)
        self.main_frame.columnconfigure(1, weight=1)
        self.main_frame.rowconfigure(0, weight=1)
        # `sticky` в .ui для sidebar/content внутри main_frame не
        # задан (Pygubu при отсутствии layout-блока оставляет его
        # пустым), поэтому grid-виджеты не растягиваются на всю
        # высоту/ширину ячейки. Принудительно включаем «nsew» и
        # фиксируем позицию: sidebar — column=0, content — column=1,
        # оба в row=0. Без явной расстановки pygubu кладёт оба в
        # (row=0,column=0) и (row=1,column=0) — это типичная грабля.
        self.sidebar_frame = self.builder.get_object(
            "sidebar_frame", self.window
        )
        self.content_frame = self.builder.get_object(
            "content_frame", self.window
        )
        self.sidebar_frame.grid_configure(
            row=0, column=0, sticky="nsew", padx=12, pady=12
        )
        self.content_frame.grid_configure(
            row=0, column=1, sticky="nsew", padx=12, pady=12
        )

        # ---- Привязка виджетов по stable id (контракт фазы 3+7) ----
        # Все id зафиксированы в `window_app.ui`. Если какой-то id
        # переименуют в .ui, `builder.get_object` поднимет KeyError —
        # это правильный fail-fast на стадии разработки.
        self.output_text: ctk.CTkTextbox = self.builder.get_object(
            "output_text", self.window
        )
        self.run_button: ctk.CTkButton = self.builder.get_object(
            "run_button", self.window
        )
        self.clear_button: ctk.CTkButton = self.builder.get_object(
            "clear_button", self.window
        )
        self.copy_button: ctk.CTkButton = self.builder.get_object(
            "copy_button", self.window
        )
        self.progressbar: ctk.CTkProgressbar = self.builder.get_object(
            "progressbar", self.window
        )
        self.status_label: ctk.CTkLabel = self.builder.get_object(
            "status_label", self.window
        )
        self.search_entry: ctk.CTkEntry = self.builder.get_object(
            "search_entry", self.window
        )
        self.search_counter: ctk.CTkLabel = self.builder.get_object(
            "search_counter", self.window
        )
        self.cards_scroll: ctk.CTkScrollableFrame = self.builder.get_object(
            "cards_scroll", self.window
        )
        self.example_title: ctk.CTkLabel = self.builder.get_object(
            "example_title", self.window
        )
        self.example_desc: ctk.CTkLabel = self.builder.get_object(
            "example_desc", self.window
        )
        self.clear_before_run_switch: ctk.CTkSwitch = self.builder.get_object(
            "clear_before_run_switch", self.window
        )
        self.autoscroll_switch: ctk.CTkSwitch = self.builder.get_object(
            "autoscroll_switch", self.window
        )
        self.metric_registry_value: ctk.CTkLabel = self.builder.get_object(
            "metric_registry_value", self.window
        )
        self.metric_last_run_value: ctk.CTkLabel = self.builder.get_object(
            "metric_last_run_value", self.window
        )
        self.metric_status_value: ctk.CTkLabel = self.builder.get_object(
            "metric_status_value", self.window
        )

        # ---- Настройка grid-весов в сайдбаре и контенте ----
        # Сайдбар: 4 строки; растягивается только строка 3 (cards_scroll).
        for r in (0, 1, 2):
            self.sidebar_frame.rowconfigure(r, weight=0)
        self.sidebar_frame.rowconfigure(3, weight=1)
        self.sidebar_frame.columnconfigure(0, weight=0)

        # Контент: 7 строк; растягивается только строка 3 (output_text).
        for r in (0, 1, 2, 4, 5, 6):
            self.content_frame.rowconfigure(r, weight=0)
        self.content_frame.rowconfigure(3, weight=1)
        self.content_frame.columnconfigure(0, weight=0)

        # ---- Реестр примеров и словари поиска ----
        # `example_id` (стабильный ключ) ↔ `title` (человекочитаемый
        # текст для статусной строки). Берём из `example_runner`,
        # чтобы имена не дублировались в UI-коде.
        examples: list[ExampleDescriptor] = list_examples()
        self._examples_by_id: dict[str, ExampleDescriptor] = {
            descriptor.example_id: descriptor for descriptor in examples
        }
        self._id_to_title: dict[str, str] = {
            descriptor.example_id: descriptor.title for descriptor in examples
        }
        self._total_examples: int = len(self._examples_by_id)

        # ---- Карточки: id → CTkFrame + его дочерние label'ы ----
        # `card_{example_id}` уже задан в .ui (фаза 3). Внутри
        # каждой карточки — два CTkLabel: `card_title_*`, `card_desc_*`.
        # Их id резолвятся здесь, чтобы навесить bind'ы (клик по
        # тексту карточки тоже выбирает пример).
        self._cards: dict[str, ctk.CTkFrame] = {}
        self._card_labels: dict[str, list[ctk.CTkLabel]] = {}
        for example_id in self._examples_by_id:
            card = self.builder.get_object(
                f"card_{example_id}", self.window
            )
            self._cards[example_id] = card

            labels: list[ctk.CTkLabel] = []
            for label_id in (
                f"card_title_{example_id}",
                f"card_desc_{example_id}",
            ):
                label_widget = self.builder.get_object(
                    label_id, self.window
                )
                labels.append(label_widget)
            self._card_labels[example_id] = labels

            # Bind на саму карточку и на её label'ы. CTkFrame
            # наследует `bind` от tkinter.Frame, поэтому
            # `<Button-1>`/`<Enter>`/`<Leave>` работают штатно.
            self._bind_card_events(card, example_id, labels)

        # ---- Состояние выбора ----
        # Текущий выбранный пример; `None` — ничего не выбрано.
        self._selected_example_id: str | None = None
        # Текущее состояние hover: `True`, если курсор внутри карточки.
        # Без этого признака Leave на дочернем label мог бы перетереть
        # hover-цвет раньше Enter на родителе.
        self._hover_card_id: str | None = None

        # ---- Поиск: StringVar + trace ----
        # `CTkEntry` поддерживает `textvariable` (CTkVariable или
        # обычный `tk.StringVar`). Используем `tk.StringVar` —
        # у `trace_add` тот же интерфейс, что и в tkinter.
        self._search_text: str = ""
        self._search_var = tk.StringVar()
        self.search_entry.configure(textvariable=self._search_var)
        self._search_var.trace_add("write", self._on_search_changed)

        # ---- Очередь и состояние воркера ----
        # Очередь между фоновым потоком и главным потоком Tk. Поток
        # кладёт кортежи `(kind, payload)`, где kind ∈ {"done", "error"}.
        self._queue: queue.Queue[tuple[str, object]] = queue.Queue()
        # Активный поток-исполнитель примера (None, если ничего не идёт).
        self._worker: threading.Thread | None = None

        # ---- Свитчи: стартовое состояние ----
        # По дизайн-спецификации оба свитча по умолчанию включены:
        # «Очистка перед запуском» удобна в большинстве сценариев,
        # «Автопрокрутка вывода» — привычное поведение терминала.
        # CTkSwitch в pygubu не подхватывает переменную `variable`
        # из .ui автоматически, поэтому состояние on задаётся кодом
        # через `select()` сразу после `get_object`.
        self.clear_before_run_switch.select()
        self.autoscroll_switch.select()

        # ---- Метрики: стартовое состояние ----
        self.metric_registry_value.configure(
            text=str(self._total_examples)
        )
        self.metric_last_run_value.configure(text=_METRIC_LAST_RUN_INITIAL)
        self.metric_status_value.configure(text=_METRIC_STATUS_INITIAL)
        self.search_counter.configure(text=_SEARCH_COUNTER_ALL)

        # ---- Шапка: стартовое состояние ----
        # До выбора примера показываем общий плейсхолдер.
        self.example_title.configure(text="Выберите пример")
        self.example_desc.configure(
            text="Кликните по карточке слева, чтобы выбрать пример"
        )

        # ---- Стартовое состояние ----
        # `progressbar` в indeterminate-режиме не двигается без
        # `start()`; явный `stop()` при инициализации — страховка от
        # визуального «застрявшего» заполнения, если .ui когда-нибудь
        # изменят.
        self.progressbar.stop()
        self._set_status(_STATUS_READY)
        self._set_running(False)
        # Все карточки по умолчанию не выбраны — применяем стартовый
        # вид (без hover, без выделения).
        for example_id in self._cards:
            self._apply_card_appearance(example_id)

        # ---- Подключение обработчиков ----
        self.run_button.configure(command=self._on_run_clicked)
        self.clear_button.configure(command=self._on_clear_clicked)
        self.copy_button.configure(command=self._on_copy_clicked)
        # Текст кнопок фиксируем в коде, чтобы он не зависел от .ui
        # (.ui их тоже задаёт, но дубль здесь — защита от рассинхрона).
        self.run_button.configure(text=_BUTTON_RUN_TEXT)
        self.clear_button.configure(text=_BUTTON_CLEAR_TEXT)
        self.copy_button.configure(text=_BUTTON_COPY_TEXT)

        # Закрытие окна крестиком — корректно завершаем mainloop,
        # не оставляя висящих потоков (daemon-потоки и так умрут
        # вместе с процессом, но явный `quit` правильнее для
        # qa/adversary).
        self.window.protocol("WM_DELETE_WINDOW", self._on_close)

    # ----------------------------------------------------------------
    # Управление состоянием UI
    # ----------------------------------------------------------------
    def _set_status(self, text: str) -> None:
        """Установить текст статусной строки. Вызывать из главного потока."""
        self.status_label.configure(text=text)

    def _set_metric_status(self, text: str, *, error: bool = False) -> None:
        """Обновить значение метрики «Статус» и, опционально, её цвет.

        Цвет берётся из палитры Tokyo Night: `c0caf5` (нейтральный)
        для обычных состояний и `f7768e` (красный) для ошибки. Это
        делает ошибку заметной даже без чтения status_label внизу.
        """
        color = _COLOR_METRIC_ERROR if error else _COLOR_METRIC_STATUS
        self.metric_status_value.configure(text=text, text_color=color)

    def _set_running(self, running: bool) -> None:
        """Переключить блокировку UI на время выполнения примера.

        Блокируем кнопку запуска, чтобы не запустить пример повторно,
        пока старый поток ещё не вернул результат. Поле поиска и
        карточки блокируем через их состояние; в CustomTkinter для
        CTkEntry и CTkSwitch есть `state` ("normal"/"disabled"), для
        CTkFrame — bind на `<Button-1>`/`<Enter>`/`<Leave>` снимается
        через `unbind` (мы временно отключаем клики, чтобы нельзя
        было переключить пример посреди выполнения).
        """
        if running:
            self.run_button.configure(
                state="disabled",
                text=_BUTTON_RUN_RUNNING,
            )
            self.search_entry.configure(state="disabled")
            # Свитчи оставляем доступными: их состояние не влияет
            # на текущий прогон (очистка — в начале, автоскролл —
            # при выводе), а пользователю удобно переключить их
            # заранее для следующего запуска.
            self._set_cards_bind_enabled(False)
        else:
            self.run_button.configure(
                state="normal",
                text=_BUTTON_RUN_TEXT,
            )
            self.search_entry.configure(state="normal")
            self._set_cards_bind_enabled(True)

    def _set_cards_bind_enabled(self, enabled: bool) -> None:
        """Включить/выключить bind'ы карточек на время выполнения примера.

        Без отключения клик по карточке во время выполнения мог бы
        переключить `_selected_example_id`, и пользователь ожидал бы,
        что следующий запуск — это новый пример. Воркер при этом
        уже работает со старым id — проще запретить клик.
        """
        for example_id, card in self._cards.items():
            labels = self._card_labels[example_id]
            for widget in (card, *labels):
                if enabled:
                    self._bind_card_events(card, example_id, labels)
                else:
                    # `unbind` на конкретный sequence снимает только его.
                    for sequence in ("<Button-1>", "<Enter>", "<Leave>"):
                        widget.unbind(sequence)

    def _append_output(self, text: str) -> None:
        """Дописать текст в конец `output_text`. Только из главного потока.

        В конце — автопрокрутка к последней строке, чтобы пользователь
        видел свежий вывод без ручного скролла. Автопрокрутка
        подчиняется свитчу `autoscroll_switch` (см. контракт фазы 7).
        CTkTextbox наследует tk.Text-совместимый интерфейс, поэтому
        `insert`/`see` работают так же, как в стандартном Text.
        """
        # `state` у CTkTextbox по умолчанию normal в .ui; на всякий
        # случай принудительно выставляем normal перед записью.
        self.output_text.configure(state="normal")
        self.output_text.insert("end", text)
        if self._autoscroll_enabled():
            self.output_text.see("end")

    def _autoscroll_enabled(self) -> bool:
        """Сообщить, включён ли свитч автопрокрутки.

        `CTkSwitch.get()` возвращает 1/0 в большинстве версий
        CustomTkinter; запасной путь — `.cget("state")` на связанной
        tkinter-переменной отсутствует (свитч не привязан к variable),
        поэтому опираемся на `get()`. Если API поменяется — `get`
        вернёт не-число, и мы тихо считаем свитч выключенным.
        """
        try:
            value = self.autoscroll_switch.get()
        except Exception:
            return False
        try:
            return int(value) == 1
        except (TypeError, ValueError):
            return bool(value)

    def _clear_output(self) -> None:
        """Очистить `output_text`. Только из главного потока."""
        self.output_text.configure(state="normal")
        self.output_text.delete("1.0", "end")

    def _copy_output_to_clipboard(self) -> bool:
        """Скопировать содержимое `output_text` в буфер обмена.

        Используем `clipboard_clear` + `clipboard_append` от
        tkinter-корня: в CustomTkinter clipboard живёт на `Tk`,
        а у `CTk` это `self.window._apply_appearance_mode` /
        `self.window.clipboard_*` (наследник `tk.Tk`). Возвращаем
        `False`, если в `output_text` пусто (тогда не трогаем буфер).
        """
        content = self.output_text.get("1.0", "end-1c")
        if not content:
            return False
        self.window.clipboard_clear()
        self.window.clipboard_append(content)
        # `update_idletasks` форсирует обработку событий буфера обмена
        # до того, как окно/процесс закроется — без этого на некоторых
        # платформах вставка после `quit` теряет содержимое.
        self.window.update_idletasks()
        return True

    # ----------------------------------------------------------------
    # Карточки: выбор, hover, пересчёт внешнего вида
    # ----------------------------------------------------------------
    def _bind_card_events(
        self,
        card: ctk.CTkFrame,
        example_id: str,
        labels: list[ctk.CTkLabel],
    ) -> None:
        """Навесить bind'ы `<Button-1>`/`<Enter>`/`<Leave>` на карточку.

        Bind'ы навешиваются и на сам фрейм, и на каждый дочерний
        label: иначе клик/наведение по тексту карточки «проваливался»
        бы и не срабатывал (label перехватывает события).
        """
        for widget in (card, *labels):
            widget.bind(
                "<Button-1>",
                lambda _event, eid=example_id: self._on_card_click(eid),
            )
            widget.bind(
                "<Enter>",
                lambda _event, eid=example_id: self._on_card_enter(eid),
            )
            widget.bind(
                "<Leave>",
                lambda _event, eid=example_id: self._on_card_leave(eid),
            )

    def _on_card_click(self, example_id: str) -> None:
        """Клик по карточке: выбрать пример и обновить шапку.

        Подсвечиваем новую карточку и снимаем подсветку со старой.
        Шапка (example_title / example_desc) обновляется сразу, чтобы
        пользователь видел, что именно выбрано, ещё до клика «Запустить».
        """
        self._set_selected(example_id)
        self._update_header(example_id)

    def _update_header(self, example_id: str) -> None:
        """Обновить шапку (`example_title` / `example_desc`) под пример."""
        title = self._id_to_title.get(example_id, example_id)
        description = _EXAMPLE_DESCRIPTIONS.get(
            example_id, "Описание недоступно"
        )
        self.example_title.configure(text=title)
        self.example_desc.configure(text=description)

    def _set_selected(self, example_id: str) -> None:
        """Сменить выбранный пример: подсветка карточки + статус."""
        previous_id = self._selected_example_id
        self._selected_example_id = example_id
        if previous_id is not None and previous_id in self._cards:
            self._apply_card_appearance(previous_id)
        if example_id in self._cards:
            self._apply_card_appearance(example_id)
        self._set_status(f"Выбран: {self._id_to_title[example_id]}")

    def _on_card_enter(self, example_id: str) -> None:
        """Курсор вошёл в карточку: применяем hover-цвет."""
        self._hover_card_id = example_id
        self._apply_card_appearance(example_id)

    def _on_card_leave(self, example_id: str) -> None:
        """Курсор покинул карточку: снимаем hover-цвет.

        Если мышь «переехала» на дочерний label той же карточки,
        Leave на родителе срабатывает раньше, чем Enter на label'е
        (или одновременно с ним) — актуальный hover_id обновится
        в `_on_card_enter` следующим тиком, и финальный цвет будет
        корректным.
        """
        if self._hover_card_id == example_id:
            self._hover_card_id = None
        self._apply_card_appearance(example_id)

    def _apply_card_appearance(self, example_id: str) -> None:
        """Пересчитать цвета карточки по (selected, hover).

        Приоритет: selected > hover > default.
        - selected=True: подсвеченный (border `#7aa2f7`, fg `#2f334d`).
        - selected=False, hover=True: чуть светлее дефолта (`#363e59`).
        - selected=False, hover=False: базовые цвета (`#292e42`/`#3b4261`).
        """
        if example_id not in self._cards:
            return
        card = self._cards[example_id]
        is_selected = example_id == self._selected_example_id
        is_hovered = example_id == self._hover_card_id

        if is_selected:
            border = _COLOR_CARD_SELECTED_BORDER
            fg = _COLOR_CARD_SELECTED_FG
        elif is_hovered:
            border = _COLOR_CARD_BORDER
            fg = _COLOR_CARD_HOVER
        else:
            border = _COLOR_CARD_BORDER
            fg = _COLOR_CARD_FG

        card.configure(border_color=border, fg_color=fg)

    # ----------------------------------------------------------------
    # Фильтрация карточек поиском
    # ----------------------------------------------------------------
    def _on_search_changed(self, *_args: object) -> None:
        """Обработчик изменения `search_entry`: фильтрует карточки.

        Фильтрация по подстроке (case-insensitive) по title или
        description примера. Видимость переключаем через
        `grid_remove()` / `grid()` — карточки уже разложены grid'ом
        в `cards_scroll` (фаза 3, .ui). `grid_remove()` сохраняет
        настройки grid, в отличие от `grid_forget()`: при показе
        карточки вернутся на те же позиции.

        Также обновляет `search_counter` в формате «Найдено: N из 5».
        """
        new_text = self._search_var.get()
        if new_text == self._search_text:
            # `trace_add` иногда срабатывает на идентичное значение
            # (например, при программном `set`). Выходим без работы.
            return
        self._search_text = new_text

        query = new_text.strip().lower()
        visible_count = 0
        for example_id, descriptor in self._examples_by_id.items():
            card = self._cards[example_id]
            if not query:
                visible = True
            else:
                title = descriptor.title.lower()
                # В реестре дескрипторов нет поля `description`,
                # поэтому берём текст из label'а — он совпадает
                # с тем, что в .ui.
                desc_label = self._card_labels[example_id][1]
                description = desc_label.cget("text").lower()
                visible = (query in title) or (query in description)
            if visible:
                visible_count += 1
                # На случай, если ранее карточка была спрятана —
                # `grid()` восстановит её по сохранённым опциям.
                card.grid()
            else:
                card.grid_remove()

        # Счётчик «Найдено: N из M» — обновляется каждый раз.
        self.search_counter.configure(
            text=f"Найдено: {visible_count} из {self._total_examples}"
        )

        # Если скрыли выбранную карточку — статус остаётся
        # («Выбран: ...»). Намеренно не сбрасываем выбор: пользователь
        # может очистить строку поиска и продолжить.

    # ----------------------------------------------------------------
    # Запуск примера в потоке
    # ----------------------------------------------------------------
    def _on_run_clicked(self) -> None:
        """Кнопка «Запустить»: проверить выбор и стартовать воркер.

        Уважает свитч `clear_before_run_switch`: если он включён —
        `output_text` очищается перед запуском (даже если предыдущий
        прогон завершился с ошибкой, чтобы видеть только новый вывод).
        """
        if self._worker is not None:
            # Дублирующий клик, пока воркер жив. `_set_running(False)`
            # при предыдущем завершении уже разблокировал кнопку,
            # так что в норме сюда не попадаем — но это дешёвая защита
            # от гонки между `after` и кликом.
            return

        example_id = self._selected_example_id
        if example_id is None:
            self._set_status(_STATUS_NO_SELECTION)
            # В `output_text` ничего не пишем — по контракту фазы 4
            # статус достаточно.
            return

        if self._clear_before_run_enabled():
            self._clear_output()
        self._start_example(example_id)

    def _clear_before_run_enabled(self) -> bool:
        """Сообщить, включён ли свитч «Очистка перед запуском»."""
        try:
            value = self.clear_before_run_switch.get()
        except Exception:
            # На старых версиях CTk `get` мог отсутствовать — считаем
            # свитч выключенным, чтобы случайно не терять предыдущий
            # вывод.
            return False
        try:
            return int(value) == 1
        except (TypeError, ValueError):
            return bool(value)

    def _start_example(self, example_id: str) -> None:
        """Подготовить UI и запустить пример `example_id` в потоке.

        1. Проверить, что воркера нет (идемпотентность).
        2. Заблокировать UI, очистить `output_text` (если пользователь
           выключил «Очистку перед запуском» — там уже очищено;
           иначе очистка делается в `_on_run_clicked`).
        3. Выставить статус «Выполняется...» и обновить метрику.
        4. Запустить `progressbar.start(...)` — `indeterminate` крутит
           «бегущий» индикатор; передаём `_QUEUE_POLL_MS`, чтобы шаг
           анимации совпадал с интервалом опроса.
        5. Создать daemon-поток и положить его в `self._worker`.
        6. Запланировать `_poll_queue` через `self.window.after`.
        """
        if self._worker is not None:
            return

        # Блокируем UI до возврата воркера.
        self._set_running(True)
        if not self._clear_before_run_enabled():
            # Свитч «очистка» выключен — очищаем здесь, чтобы свежий
            # прогон не перемешивался со старым выводом (заголовок
            # «=== Запуск: ...» появится всегда; он маркирует начало).
            self._clear_output()
        title = self._id_to_title.get(example_id, example_id)
        self._set_status(_STATUS_RUNNING)
        self._set_metric_status(_STATUS_RUNNING)
        # CTk 6.0.0: `CTkProgressBar.start()` не принимает аргументов
        # (интервал анимации встроен в реализацию `_internal_loop`).
        # Передача `_QUEUE_POLL_MS` роняла `TypeError` (см. DEF-001).
        self.progressbar.start()

        # Daemon-поток: при завершении процесса поток не помешает
        # выходу; при обычной работе его состояние держим в
        # `self._worker` и якорим из главного потока.
        # Старт воркера и `after(...)` обёрнуты в try/except: если
        # что-то пойдёт не так уже после блокировки UI, откатим
        # состояние (разблокируем кнопку, остановим прогресс), чтобы
        # пользователь не остался в «прерванном» режиме. Заголовок
        # `=== Запуск: ... ===` пишем только при успешном старте —
        # раньше он оставался в output_text артефактом полузапуска
        # (см. ADV-006).
        try:
            self._worker = threading.Thread(
                target=self._run_in_worker,
                args=(example_id,),
                name=f"example-runner-{example_id}",
                daemon=True,
            )
            self._worker.start()
        except Exception:
            self.progressbar.stop()
            self._set_running(False)
            self._set_status(_STATUS_ERROR)
            self._set_metric_status(_STATUS_ERROR, error=True)
            self._worker = None
            raise

        # Заголовок вывода — после успешного старта воркера, чтобы
        # исключение при `Thread()` не оставляло «голый» заголовок.
        self._append_output(f"=== Запуск: {title} ({example_id}) ===\n")

        # `after` из главного потока Tk. Возвращаемое значение
        # (id таймера) нам не нужно: `cancel` не предусмотрен —
        # `_poll_queue` сам перестаёт планировать себя, когда
        # воркер завершился и очередь пуста.
        self.window.after(_QUEUE_POLL_MS, self._poll_queue)

    def _run_in_worker(self, example_id: str) -> None:
        """Тело фонового потока: вызвать `run_example` и положить результат.

        `run_example` пробрасывает исключения примера дальше.
        Оборачиваем вызов `try/except`, чтобы окно не падало, а
        traceback попал в `output_text` как обычный вывод. В очередь
        кладём кортеж `(kind, payload)`: kind — `"done"` (с готовой
        строкой) или `"error"` (с traceback).
        """
        try:
            result = run_example(example_id)
        except Exception:
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
          `status_label`, метрики, сбрасываем `self._worker = None`.
        - Если воркер уже завершился и очередь пуста — на этом
          опрос заканчивается (новых `after` не планируем).
        - В любом другом случае (воркер жив, очередь пуста) —
          планируем следующий опрос.
        """
        terminal: tuple[str, object] | None = None
        last_example_id: str | None = (
            self._selected_example_id
            if self._selected_example_id is not None
            else None
        )
        try:
            while True:
                kind, payload = self._queue.get_nowait()
                if kind == "done":
                    self._append_output(str(payload))
                    terminal = (kind, payload)
                elif kind == "error":
                    self._append_output(f"[ОШИБКА]\n{payload}\n")
                    terminal = (kind, payload)
                else:
                    # Неизвестный kind — логируем и считаем терминалом,
                    # чтобы окно не «зависло» в режиме выполнения.
                    import logging
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
                self._set_metric_status(_STATUS_DONE)
                # Метрика «Последний запуск» — название + локальное время.
                self._update_last_run_metric(last_example_id)
            else:
                self._set_status(_STATUS_ERROR)
                self._set_metric_status(_STATUS_ERROR, error=True)
            self._worker = None
            return

        # Нетерминальный опрос: воркер ещё работает либо только что
        # завершился, но сообщение ещё не дошло. Планируем следующий
        # тик, пока воркер жив, и один «дожим» после завершения.
        if self._worker is not None or not self._queue.empty():
            self.window.after(_QUEUE_POLL_MS, self._poll_queue)
        else:
            # Ни воркера, ни сообщений — но терминала мы не получили.
            # Чистим только прогресс и блокировку UI, статус не трогаем.
            self.progressbar.stop()
            self._set_running(False)

    def _update_last_run_metric(self, example_id: str | None) -> None:
        """Обновить метрику «Последний запуск»: название (HH:MM:SS)."""
        if example_id is None or example_id not in self._id_to_title:
            return
        title = self._id_to_title[example_id]
        timestamp = _dt.datetime.now().strftime("%H:%M:%S")
        self.metric_last_run_value.configure(
            text=f"{title} ({timestamp})"
        )

    # ----------------------------------------------------------------
    # Кнопки: очистка, копирование, закрытие
    # ----------------------------------------------------------------
    def _on_clear_clicked(self) -> None:
        """Кнопка «Очистить»: стереть `output_text` и сбросить статус.

        Статус сбрасывается на «Готово» (а не на «Выбран: ...»), потому
        что пользователь явно нажал «Очистить» — это жест сброса
        рабочей области, а не жест «сними выделение». Сам выбор
        (если был) сохраняем.
        """
        self._clear_output()
        self._set_status(_STATUS_READY)

    def _on_copy_clicked(self) -> None:
        """Кнопка «Копировать»: перенести `output_text` в clipboard.

        При успехе — короткий статус «Вывод скопирован» (по контракту
        фазы 7 «не нужно возвращать прежний статус» — пользователь
        увидит подтверждение и продолжит работу). При пустом выводе —
        статус «Нечего копировать», буфер обмена не трогаем.
        """
        if self._copy_output_to_clipboard():
            self._set_status(_STATUS_COPIED)
        else:
            self._set_status(_STATUS_COPIED_EMPTY)

    def _on_close(self) -> None:
        """Обработчик закрытия окна (крестик): корректно выйти из mainloop.

        `self._worker` — daemon-поток; при выходе из процесса он и так
        умрёт. Явный `quit` нужен, чтобы `mainloop` вернул управление
        вызывающему коду, а не оставил окно «висеть» в фоне.
        """
        self.window.quit()
