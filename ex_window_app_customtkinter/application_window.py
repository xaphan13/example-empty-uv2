"""Оконный класс `ApplicationWindow` для пакета `ex_window_app_customtkinter`.

Назначение:
- загрузить разметку из `window_app.ui` через `pygubu.Builder`;
- встроить её в `customtkinter.CTk` с тёмной темой «blue»;
- связать виджеты по stable id с обработчиками;
- запускать курируемые примеры из `example_runner.run_example` в
  фоновом потоке, доставляя вывод в `output_text` через `queue.Queue`
  и `window.after(...)` (обязательно из главного потока Tk).

Редизайн v3 «Aurora Night» — что добавилось сверх запуска примеров:

- **Парение (hover-анимации).** Все кнопки и карточки реагируют на
  курсор плавным переходом цвета (интерполяция hex через `after`),
  а не мгновенной сменой `hover_color`. Встроенный hover у кнопок
  отключён (`hover=false` в .ui) — анимирует код.
- **FAB (floating action button).** Круглая кнопка «▶» в правом
  нижнем углу окна (place поверх grid): быстрый запуск выбранного
  примера, постоянная пульсация и «подъём» при наведении.
- **Симуляция задач.** Три фейковые задачи («Загрузка данных»,
  «Обработка», «Экспорт») с собственными прогрессбарами и процентами;
  скорость регулируется слайдером. Работают параллельно, «Тест»
  запускает их цепочкой. Всё через `after` — без потоков.
- **Демо-кнопки.** «Тост» (временный статус), «Волна» (поочерёдная
  подсветка кнопок), «Вспышка» (подсветка карточек метрик),
  «Сброс» (полный сброс состояния), «Тест» (цепочка задач).
- **Метрики.** 4 мини-карточки: примеров в реестре, счётчик запусков,
  живые часы (тик раз в секунду), статус.
- **Оформление.** Переключатель темы (Тёмная/Светлая/Система) с
  перекраской поверхностей и выбор акцентного цвета (5 палитр),
  перекрашивающий кнопки/прогрессбары/слайдер/FAB на лету.
- **Цветной терминал.** Заголовки прогонов и ошибки подсвечиваются
  тегами tk.Text.

Анимации реализованы пошагово через `window.after` (без потоков и
без внешних зависимостей): `_animate` интерполирует цвет свойства
виджета за ~160 мс; конкурирующие анимации одного свойства отменяют
друг друга (ключ = пара «виджет, свойство»).

Импорт модуля безопасен для headless-сред: никакие GUI-объекты
(`Tk`, `CTk`, загрузка `.ui`) не создаются на уровне модуля — только
при вызове `ApplicationWindow(...)`.
"""

from __future__ import annotations

import customtkinter as ctk
import datetime as _dt
import pygubu
import queue
import re
import threading
import tkinter as tk
import traceback
from pathlib import Path
from typing import Callable, Final

from ex_window_app_customtkinter.example_runner import (
    ExampleDescriptor,
    list_examples,
    run_example,
)


# ------------------------------------------------------------------------
# Константы
# ------------------------------------------------------------------------
# Тема CustomTkinter — стартово тёмная; дальше переключается сегментом
# «Оформление» в UI (Тёмная/Светлая/Система).
_APPEARANCE_MODE: Final[str] = "Dark"
_COLOR_THEME: Final[str] = "blue"

# Заголовок и геометрия окна (редизайн v3: 980x640, minsize 900x560).
_WINDOW_TITLE: Final[str] = "CustomTkinter — запуск примеров"
_WINDOW_GEOMETRY: Final[str] = "980x640"
_WINDOW_MINSIZE: Final[tuple[int, int]] = (900, 560)

# ----------------------------------------------------------------
# Палитры «Aurora Night». Единая точка правды: .ui содержит те же
# тёмные значения, а код использует словарь для перекраски при
# смене темы и для hover-анимаций (цвета берутся из активной
# палитры в момент события).
# ----------------------------------------------------------------
_PALETTE_DARK: Final[dict[str, str]] = {
    "bg_app": "#0b0e14",
    "panel": "#11151f",
    "card": "#171c29",
    "card_hover": "#232c42",
    "card_selected": "#1c2438",
    "card_selected_border": "#6d8dff",
    "input": "#141926",
    "border": "#272f42",
    "border_hover": "#42507a",
    "track": "#1d2434",
    "term_bg": "#070a10",
    "term_fg": "#c8d3f5",
    "text": "#d7defc",
    "text_bright": "#ffffff",
    "text_dim": "#7d87a8",
    "text_dim2": "#565f7d",
    "text_ghost": "#3f4763",
    "on_accent": "#0b0e14",
}

# Светлая тема: перекрашиваются только крупные поверхности и тексты;
# акцентные цвета (кнопка запуска, прогрессбары) остаются яркими.
_PALETTE_LIGHT: Final[dict[str, str]] = {
    "bg_app": "#e8ecf6",
    "panel": "#ffffff",
    "card": "#f2f5fc",
    "card_hover": "#e4eaf8",
    "card_selected": "#e7edff",
    "card_selected_border": "#6d8dff",
    "input": "#eef1f8",
    "border": "#d5dcee",
    "border_hover": "#a9b8e0",
    "track": "#e4e9f4",
    "term_bg": "#f7f9ff",
    "term_fg": "#2a3350",
    "text": "#2a3350",
    "text_bright": "#101528",
    "text_dim": "#6b7492",
    "text_dim2": "#8a93b2",
    "text_ghost": "#b4bdd6",
    "on_accent": "#0b0e14",
}

# Акцентные палитры: имя → (базовый, hover). Выбираются OptionMenu
# «Акцент»; применяются к run/FAB/прогрессбарам/слайдеру/свитчам.
_ACCENTS: Final[dict[str, tuple[str, str]]] = {
    "Синий": ("#6d8dff", "#8aa2ff"),
    "Циан": ("#4cc9f0", "#7ad9f7"),
    "Зелёный": ("#3ddc97", "#6fe7b5"),
    "Розовый": ("#ff6b9d", "#ff8fb4"),
    "Янтарный": ("#ffd166", "#ffe08f"),
}
_DEFAULT_ACCENT: Final[str] = "Синий"

# Тексты задач — синхронны с .ui (task_run_N / task_name_N).
_TASK_TITLES: Final[tuple[str, ...]] = (
    "Загрузка данных",
    "Обработка",
    "Экспорт",
)

# Соответствие «имя в сегменте» → режим CustomTkinter.
_THEME_MODES: Final[dict[str, str]] = {
    "Тёмная": "Dark",
    "Светлая": "Light",
    "Система": "System",
}

# Интервал опроса очереди из главного потока (мс). 100 мс — баланс
# между отзывчивостью UI и нагрузкой на event loop.
_QUEUE_POLL_MS: Final[int] = 100

# Часы: период обновления метрики «Время».
_CLOCK_TICK_MS: Final[int] = 1000

# Анимации: шаг и длительность по умолчанию (мс). 16 мс ≈ 60 fps.
_ANIM_STEP_MS: Final[int] = 16
_ANIM_DURATION_MS: Final[int] = 160

# Пульс FAB: период полного цикла «дыхания».
_FAB_PULSE_MS: Final[int] = 2400

# Тексты статусов — единая точка правды, чтобы qa/adversary могли
# проверять состояние окна по строке.
_STATUS_READY: Final[str] = "Готово"
_STATUS_RUNNING: Final[str] = "Выполняется..."
_STATUS_DONE: Final[str] = "Завершено"
_STATUS_ERROR: Final[str] = "Ошибка"
_STATUS_NO_SELECTION: Final[str] = "Сначала выберите пример"
_STATUS_COPIED: Final[str] = "Вывод скопирован"
_STATUS_COPIED_EMPTY: Final[str] = "Нечего копировать"
_STATUS_RESET: Final[str] = "Состояние сброшено"

# Тексты кнопок по умолчанию.
_BUTTON_RUN_TEXT: Final[str] = "▶  Запустить"
_BUTTON_RUN_RUNNING: Final[str] = "Выполняется..."
_BUTTON_CLEAR_TEXT: Final[str] = "Очистить"
_BUTTON_COPY_TEXT: Final[str] = "Копировать"

_METRIC_REGISTRY_INITIAL: Final[str] = "5"
_METRIC_STATUS_INITIAL: Final[str] = "Готово"
_SEARCH_COUNTER_ALL: Final[str] = "Найдено: 5 из 5"

# Шаблоны вывода терминала (теги: hdr — заголовки, err — ошибки).
_TAG_HDR: Final[str] = "hdr"
_TAG_ERR: Final[str] = "err"

# Имя .ui-файла лежит рядом с этим модулем. Путь разрешается через
# `Path(__file__).with_name(...)`, чтобы не зависеть от cwd — см.
# «cwd-зависимость» в AGENTS.md.
_UI_FILENAME: Final[str] = "window_app.ui"

# Регулярка валидного hex-цвета: анимировать можно только строки
# вида #rrggbb (cget иногда возвращает "transparent" или объекты).
_HEX_RE: Final[re.Pattern[str]] = re.compile(r"^#[0-9a-fA-F]{6}$")

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
# Утилиты цвета
# ------------------------------------------------------------------------
def _hex_to_rgb(color: str) -> tuple[int, int, int]:
    """`#rrggbb` → кортеж (r, g, b). Вход обязан быть валидным hex."""
    value = color.lstrip("#")
    return int(value[0:2], 16), int(value[2:4], 16), int(value[4:6], 16)


def _rgb_to_hex(rgb: tuple[int, int, int]) -> str:
    """(r, g, b) → строка `#rrggbb` (каналы зажаты в 0..255)."""
    r, g, b = (max(0, min(255, c)) for c in rgb)
    return f"#{r:02x}{g:02x}{b:02x}"


def _lerp_color(start: str, end: str, t: float) -> str:
    """Линейная интерполяция двух hex-цветов, t в [0, 1]."""
    s = _hex_to_rgb(start)
    e = _hex_to_rgb(end)
    mixed = tuple(round(s[i] + (e[i] - s[i]) * t) for i in range(3))
    return _rgb_to_hex(mixed)  # type: ignore[arg-type]


def _lighten(color: str, amount: float) -> str:
    """Осветлить hex-цвет к белому на долю amount (0..1)."""
    return _lerp_color(color, "#ffffff", amount)


# ------------------------------------------------------------------------
# ApplicationWindow
# ------------------------------------------------------------------------
class ApplicationWindow:
    """Главное окно GUI-примера: виджеты + запуск курируемых примеров.

    Жизненный цикл:
    1. `__init__` поднимает `ctk.CTk`, загружает `.ui`, привязывает
       виджеты, настраивает grid-веса, создаёт FAB и запускает
       фоновые «тикающие» сценарии (часы, пульс FAB, intro-анимация
       карточек).
    2. Вызывающий код (`main_window_app.py`) стартует
       `self.window.mainloop()`.
    3. Примеры запускаются в daemon-потоке; их вывод приходит в
       главный поток через `queue.Queue` и `_poll_queue` (after).
    4. Симуляции задач и все анимации живут в `after`-цепочках
       главного потока — никаких потоков для UI-обновлений.

    Все мутации виджетов происходят только из главного потока.

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
        # регистрации.
        self.builder = pygubu.Builder()
        self.builder.add_from_file(str(ui_path))

        # Корневой `main_frame` (CTkFrame в .ui) встраивается прямо
        # в окно. Так в одном дереве виджетов — и CTk, и CTkFrame.
        self.main_frame = self.builder.get_object("main_frame", self.window)
        self.main_frame.pack(fill="both", expand=True)

        # ---- Grid-веса (контракт редизайна v3) ----
        # Задаются кодом, потому что надёжнее layout'а из .ui:
        # pygubu иногда округляет веса. main_frame: столбец 0 —
        # сайдбар (weight 0, minsize 324 = 300 px видимой ширины +
        # padx 12+12), столбец 1 — контент (weight 1).
        self.main_frame.columnconfigure(0, weight=0, minsize=324)
        self.main_frame.columnconfigure(1, weight=1)
        self.main_frame.rowconfigure(0, weight=1)
        # `sticky` в .ui для sidebar/content не задан — расставляем
        # явно, иначе grid-виджеты не растянутся на всю ячейку.
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
            row=0, column=1, sticky="nsew", padx=(0, 12), pady=12
        )

        # ---- Привязка виджетов по stable id ----
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
        self.progressbar: ctk.CTkProgressBar = self.builder.get_object(
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
        self.metric_runs_value: ctk.CTkLabel = self.builder.get_object(
            "metric_runs_value", self.window
        )
        self.metric_clock_value: ctk.CTkLabel = self.builder.get_object(
            "metric_clock_value", self.window
        )
        self.metric_status_value: ctk.CTkLabel = self.builder.get_object(
            "metric_status_value", self.window
        )
        self.metric_card_registry: ctk.CTkFrame = self.builder.get_object(
            "metric_card_registry", self.window
        )
        self.metric_card_runs: ctk.CTkFrame = self.builder.get_object(
            "metric_card_runs", self.window
        )
        self.metric_card_clock: ctk.CTkFrame = self.builder.get_object(
            "metric_card_clock", self.window
        )
        self.metric_card_status: ctk.CTkFrame = self.builder.get_object(
            "metric_card_status", self.window
        )
        self.theme_segmented: ctk.CTkSegmentedButton = (
            self.builder.get_object("theme_segmented", self.window)
        )
        self.accent_menu: ctk.CTkOptionMenu = self.builder.get_object(
            "accent_menu", self.window
        )
        self.sidebar_title: ctk.CTkLabel = self.builder.get_object(
            "sidebar_title", self.window
        )
        self.sidebar_badge: ctk.CTkLabel = self.builder.get_object(
            "sidebar_badge", self.window
        )
        self.sidebar_footer: ctk.CTkLabel = self.builder.get_object(
            "sidebar_footer", self.window
        )
        self.tasks_frame: ctk.CTkFrame = self.builder.get_object(
            "tasks_frame", self.window
        )
        self.demo_frame: ctk.CTkFrame = self.builder.get_object(
            "demo_frame", self.window
        )
        self.speed_slider: ctk.CTkSlider = self.builder.get_object(
            "speed_slider", self.window
        )
        self.speed_value: ctk.CTkLabel = self.builder.get_object(
            "speed_value", self.window
        )
        self.task_buttons: tuple[ctk.CTkButton, ...] = tuple(
            self.builder.get_object(f"task_run_{i}", self.window)
            for i in (1, 2, 3)
        )
        self.task_bars: tuple[ctk.CTkProgressBar, ...] = tuple(
            self.builder.get_object(f"task_bar_{i}", self.window)
            for i in (1, 2, 3)
        )
        self.task_pcts: tuple[ctk.CTkLabel, ...] = tuple(
            self.builder.get_object(f"task_pct_{i}", self.window)
            for i in (1, 2, 3)
        )
        self.demo_buttons: dict[str, ctk.CTkButton] = {
            key: self.builder.get_object(f"demo_{key}", self.window)
            for key in ("toast", "wave", "flash", "reset", "test")
        }

        # ---- Настройка grid-весов в сайдбаре и контенте ----
        # Сайдбар: 5 строк; растягивается только строка 3 (cards_scroll).
        for r in (0, 1, 2, 4):
            self.sidebar_frame.rowconfigure(r, weight=0)
        self.sidebar_frame.rowconfigure(3, weight=1)
        self.sidebar_frame.columnconfigure(0, weight=1)

        # Контент: 9 строк; растягивается только строка 5 (output_text).
        for r in (0, 1, 2, 3, 4, 6, 7, 8):
            self.content_frame.rowconfigure(r, weight=0)
        self.content_frame.rowconfigure(5, weight=1)
        self.content_frame.columnconfigure(0, weight=1)

        # ---- Активная палитра и акцент ----
        # Палитра — словарь ролей; hover-анимации и перекраска темы
        # всегда читают цвета из него в момент события.
        self._palette: dict[str, str] = dict(_PALETTE_DARK)
        self._theme_name: str = "Тёмная"
        self._accent_name: str = _DEFAULT_ACCENT
        self._accent, self._accent_hover = _ACCENTS[_DEFAULT_ACCENT]

        # ---- Реестр примеров и словари поиска ----
        examples: list[ExampleDescriptor] = list_examples()
        self._examples_by_id: dict[str, ExampleDescriptor] = {
            descriptor.example_id: descriptor for descriptor in examples
        }
        self._id_to_title: dict[str, str] = {
            descriptor.example_id: descriptor.title for descriptor in examples
        }
        self._total_examples: int = len(self._examples_by_id)

        # ---- Карточки: id → CTkFrame + его дочерние label'ы ----
        self._cards: dict[str, ctk.CTkFrame] = {}
        self._card_labels: dict[str, list[ctk.CTkLabel]] = {}
        for example_id in self._examples_by_id:
            card = self.builder.get_object(f"card_{example_id}", self.window)
            self._cards[example_id] = card

            labels: list[ctk.CTkLabel] = []
            for label_id in (
                f"card_title_{example_id}",
                f"card_desc_{example_id}",
            ):
                labels.append(self.builder.get_object(label_id, self.window))
            self._card_labels[example_id] = labels

            self._bind_card_events(card, example_id, labels)

        # ---- Состояние выбора и hover ----
        self._selected_example_id: str | None = None
        self._hover_card_id: str | None = None

        # ---- Поиск: StringVar + trace ----
        self._search_text: str = ""
        self._search_var = tk.StringVar()
        self.search_entry.configure(textvariable=self._search_var)
        self._search_var.trace_add("write", self._on_search_changed)

        # ---- Очередь и состояние воркера ----
        self._queue: queue.Queue[tuple[str, object]] = queue.Queue()
        self._worker: threading.Thread | None = None

        # ---- Свитчи: стартовое состояние ----
        # CTkSwitch в pygubu не подхватывает `variable` из .ui,
        # поэтому состояние on задаётся кодом через `select()`.
        self.clear_before_run_switch.select()
        self.autoscroll_switch.select()

        # ---- Метрики и счётчики ----
        self._runs_count: int = 0
        self.metric_registry_value.configure(text=str(self._total_examples))
        self.metric_runs_value.configure(text="0")
        self.metric_clock_value.configure(text="--:--:--")
        self.metric_status_value.configure(text=_METRIC_STATUS_INITIAL)
        self.search_counter.configure(text=_SEARCH_COUNTER_ALL)

        # ---- Шапка: стартовое состояние ----
        self.example_title.configure(text="Выберите пример")
        self.example_desc.configure(
            text="Кликните по карточке слева, чтобы выбрать пример"
        )

        # ---- Тосты: активный таймер и «базовый» текст статуса ----
        self._status_text: str = _STATUS_READY
        self._toast_after_id: str | None = None

        # ---- Реестр активных анимаций ----
        # Ключ (id(widget), prop) → after-id текущей анимации.
        self._anim_jobs: dict[tuple[int, str], str] = {}
        # Флаг закрытия: все after-цепочки проверяют его и не
        # перезапланируются после quit().
        self._closing: bool = False

        # ---- Симуляции задач ----
        # На каждую задачу: флаг выполнения, текущее значение бара и
        # after-id шага анимации. Задачи независимы и идут параллельно.
        self._task_states: list[dict[str, object]] = [
            {"running": False, "value": 0.0, "after_id": None}
            for _ in _TASK_TITLES
        ]
        # Очередь цепочки для кнопки «Тест»: [1, 2] значит «после
        # задачи 0 запустить 1, затем 2».
        self._task_chain: list[int] = []

        # ---- Скорость симуляций ----
        self._speed: int = 5
        self.speed_slider.set(self._speed)
        self.speed_value.configure(text=f"{self._speed}x")

        # ---- Стартовое состояние ----
        self.progressbar.set(0)
        self._set_status(_STATUS_READY)
        self._set_running(False)
        for example_id in self._cards:
            self._apply_card_appearance(example_id)

        # ---- Терминал: теги подсветки ----
        self._configure_terminal_tags()

        # ---- Обработчики кнопок и контролов ----
        self.run_button.configure(command=self._on_run_clicked)
        self.clear_button.configure(command=self._on_clear_clicked)
        self.copy_button.configure(command=self._on_copy_clicked)
        self.run_button.configure(text=_BUTTON_RUN_TEXT)
        self.clear_button.configure(text=_BUTTON_CLEAR_TEXT)
        self.copy_button.configure(text=_BUTTON_COPY_TEXT)

        self.theme_segmented.set(self._theme_name)
        self.theme_segmented.configure(command=self._on_theme_changed)
        self.accent_menu.set(self._accent_name)
        self.accent_menu.configure(command=self._on_accent_changed)
        # pygubu-плагин не знает dropdown_fg_color — задаём кодом.
        self.accent_menu.configure(dropdown_fg_color=self._palette["card"])

        self.speed_slider.configure(command=self._on_speed_changed)
        for idx, button in enumerate(self.task_buttons):
            button.configure(
                command=lambda i=idx: self._start_task(i)
            )
        self.demo_buttons["toast"].configure(command=self._on_demo_toast)
        self.demo_buttons["wave"].configure(command=self._on_demo_wave)
        self.demo_buttons["flash"].configure(command=self._on_demo_flash)
        self.demo_buttons["reset"].configure(command=self._on_demo_reset)
        self.demo_buttons["test"].configure(command=self._on_demo_test)

        # ---- Парение: hover-анимации кнопок ----
        # Акцентная кнопка светлеет; «карточные» — светлеют и поднимают
        # бордер. Цвета берутся из палитры в момент события.
        self._bind_button_hover(self.run_button, kind="accent")
        for button in (
            self.clear_button,
            self.copy_button,
            *self.task_buttons,
            *self.demo_buttons.values(),
        ):
            self._bind_button_hover(button, kind="card")

        # ---- FAB: парящая кнопка быстрого запуска ----
        self._make_fab()

        # ---- Фоновые сценарии ----
        self._tick_clock()
        self._pulse_fab()
        self._intro_cards()

        # Закрытие окна крестиком — корректно завершаем mainloop.
        self.window.protocol("WM_DELETE_WINDOW", self._on_close)

    # ----------------------------------------------------------------
    # Анимации (ядро «парения»)
    # ----------------------------------------------------------------
    def _animate(
        self,
        widget: object,
        prop: str,
        target: str,
        duration_ms: int = _ANIM_DURATION_MS,
        on_done: Callable[[], None] | None = None,
    ) -> None:
        """Плавно интерполировать цвет свойства `prop` виджета.

        Пошаговая анимация через `after`: шаг — `_ANIM_STEP_MS`,
        всего `duration_ms / step` шагов. Конкурирующая анимация той
        же пары (виджет, свойство) отменяется — цвет всегда движется
        к последней цели.

        Если текущее значение свойства не валидный hex (например
        "transparent" или объект цвета CTk), анимация вырождается в
        мгновенный `configure` — это безопасный fallback.
        """
        key = (id(widget), prop)
        previous = self._anim_jobs.pop(key, None)
        if previous is not None:
            try:
                self.window.after_cancel(previous)
            except Exception:
                pass

        try:
            current = widget.cget(prop)  # type: ignore[attr-defined]
        except Exception:
            current = None
        if not isinstance(current, str) or not _HEX_RE.match(current):
            self._apply(widget, prop, target)
            if on_done is not None:
                on_done()
            return
        if current.lower() == target.lower():
            if on_done is not None:
                on_done()
            return

        steps = max(1, duration_ms // _ANIM_STEP_MS)

        def step(index: int) -> None:
            if self._closing:
                self._anim_jobs.pop(key, None)
                return
            t = index / steps
            self._apply(widget, prop, _lerp_color(current, target, t))
            if index < steps:
                job = self.window.after(
                    _ANIM_STEP_MS, lambda: step(index + 1)
                )
                self._anim_jobs[key] = job
            else:
                self._apply(widget, prop, target)
                self._anim_jobs.pop(key, None)
                if on_done is not None:
                    on_done()

        job = self.window.after(_ANIM_STEP_MS, lambda: step(1))
        self._anim_jobs[key] = job

    @staticmethod
    def _apply(widget: object, prop: str, value: str) -> None:
        """configure с глушением исключений для мёртвых виджетов."""
        try:
            widget.configure(**{prop: value})  # type: ignore[attr-defined]
        except Exception:
            pass

    def _bind_button_hover(
        self, button: ctk.CTkButton, *, kind: str
    ) -> None:
        """Навесить плавный hover на кнопку (встроенный отключён в .ui).

        kind="accent" — кнопка на акцентной заливке (run): hover чуть
        светлее акцента. kind="card" — кнопка-«карточка»: фон светлеет
        и бордер подсвечивается. Цвета читаются из активной палитры
        в момент события — смена темы не ломает hover.
        """
        def enter(_event: object) -> None:
            if str(button.cget("state")) == "disabled":
                return
            if kind == "accent":
                self._animate(button, "fg_color", self._accent_hover)
            else:
                self._animate(button, "fg_color", self._palette["card_hover"])
                self._animate(button, "border_color", self._palette["border_hover"])

        def leave(_event: object) -> None:
            if kind == "accent":
                self._animate(button, "fg_color", self._accent)
            else:
                self._animate(button, "fg_color", self._palette["card"])
                self._animate(button, "border_color", self._palette["border"])

        button.bind("<Enter>", enter, add="+")
        button.bind("<Leave>", leave, add="+")

    # ----------------------------------------------------------------
    # FAB (floating action button)
    # ----------------------------------------------------------------
    def _make_fab(self) -> None:
        """Создать круглую парящую кнопку поверх правого нижнего угла.

        place() позволяет наложить кнопку на grid-раскладку — это и
        есть «парение». Постоянная пульсация (`_pulse_fab`) и подъём
        при наведении делают её живой; клик — быстрый запуск
        выбранного примера.
        """
        self.fab: ctk.CTkButton = ctk.CTkButton(
            self.window,
            text="▶",
            width=54,
            height=54,
            corner_radius=27,
            fg_color=self._accent,
            hover_color=self._accent_hover,
            text_color=self._palette["on_accent"],
            font=("Arial", 18, "bold"),
            border_width=0,
            hover=False,
            command=self._on_fab_clicked,
        )
        self.fab.place(relx=1.0, rely=1.0, x=-28, y=-28, anchor="se")
        self.fab.lift()
        self._fab_lifted: bool = False
        self.fab.bind("<Enter>", self._on_fab_enter, add="+")
        self.fab.bind("<Leave>", self._on_fab_leave, add="+")

    def _on_fab_enter(self, _event: object) -> None:
        """Hover FAB: подсветка + плавный «подъём» на 8 px вверх."""
        if str(self.fab.cget("state")) == "disabled":
            return
        self._animate(self.fab, "fg_color", self._accent_hover)
        self._fab_slide(to_y=-36)

    def _on_fab_leave(self, _event: object) -> None:
        """Уход курсора с FAB: возврат цвета и позиции."""
        self._animate(self.fab, "fg_color", self._accent)
        self._fab_slide(to_y=-28)

    def _fab_slide(self, *, to_y: int) -> None:
        """Плавно сдвинуть FAB по вертикали к `to_y` (place-координата)."""
        key = (id(self.fab), "__y__")
        previous = self._anim_jobs.pop(key, None)
        if previous is not None:
            try:
                self.window.after_cancel(previous)
            except Exception:
                pass
        steps = 6
        try:
            info = self.fab.place_info()
            start_y = int(info.get("y", -28))
        except Exception:
            start_y = -28
        if start_y == to_y:
            return

        def step(index: int) -> None:
            if self._closing:
                self._anim_jobs.pop(key, None)
                return
            t = index / steps
            y = round(start_y + (to_y - start_y) * t)
            try:
                self.fab.place(y=y)
            except Exception:
                return
            if index < steps:
                self._anim_jobs[key] = self.window.after(
                    _ANIM_STEP_MS, lambda: step(index + 1)
                )
            else:
                self._anim_jobs.pop(key, None)

        self._anim_jobs[key] = self.window.after(
            _ANIM_STEP_MS, lambda: step(1)
        )

    def _pulse_fab(self) -> None:
        """Постоянное «дыхание» FAB: мягкая волна к светлому и назад.

        Планирует сам себя каждые `_FAB_PULSE_MS`. При закрытии окна
        или активном hover не перезапускается (hover сам управляет
        цветом).
        """
        if self._closing:
            return

        def back() -> None:
            self._animate(self.fab, "fg_color", self._accent, 350)

        self._animate(
            self.fab,
            "fg_color",
            _lighten(self._accent, 0.28),
            350,
            on_done=back,
        )
        self.window.after(_FAB_PULSE_MS, self._pulse_fab)

    def _on_fab_clicked(self) -> None:
        """FAB = быстрый запуск выбранного примера (дубль run_button)."""
        self._on_run_clicked()

    # ----------------------------------------------------------------
    # Часы и тосты
    # ----------------------------------------------------------------
    def _tick_clock(self) -> None:
        """Обновить метрику «Время» и запланировать следующий тик."""
        if self._closing:
            return
        self.metric_clock_value.configure(
            text=_dt.datetime.now().strftime("%H:%M:%S")
        )
        self.window.after(_CLOCK_TICK_MS, self._tick_clock)

    def _set_status(self, text: str) -> None:
        """Установить «базовый» текст статусной строки.

        Сбрасывает активный тост (он — временное сообщение поверх
        базового статуса). Вызывать из главного потока.
        """
        self._status_text = text
        if self._toast_after_id is not None:
            try:
                self.window.after_cancel(self._toast_after_id)
            except Exception:
                pass
            self._toast_after_id = None
        self.status_label.configure(
            text=text, text_color=self._palette["text_dim2"]
        )

    def _toast(self, text: str, duration_ms: int = 2600) -> None:
        """Показать временное сообщение в статусной строке.

        Через `duration_ms` вернётся базовый статус. Повторный тост
        заменяет предыдущий (таймер отменяется).
        """
        if self._toast_after_id is not None:
            try:
                self.window.after_cancel(self._toast_after_id)
            except Exception:
                pass
        self.status_label.configure(text=text, text_color=self._accent)

        def restore() -> None:
            self._toast_after_id = None
            self.status_label.configure(
                text=self._status_text,
                text_color=self._palette["text_dim2"],
            )

        self._toast_after_id = self.window.after(duration_ms, restore)

    # ----------------------------------------------------------------
    # Тема и акцент
    # ----------------------------------------------------------------
    def _on_theme_changed(self, value: str) -> None:
        """Сегмент «Оформление»: сменить режим CTk и перекрасить UI."""
        if value not in _THEME_MODES:
            return
        self._theme_name = value
        ctk.set_appearance_mode(_THEME_MODES[value])
        self._palette = dict(
            _PALETTE_LIGHT if value == "Светлая" else _PALETTE_DARK
        )
        self._apply_theme_surfaces()
        self._apply_accent(self._accent_name, toast=False)
        self._configure_terminal_tags()
        for example_id in self._cards:
            self._apply_card_appearance(example_id)
        self._toast(f"Тема: {value}")

    def _apply_theme_surfaces(self) -> None:
        """Перекрасить все поверхности и тексты под активную палитру.

        Списки собраны один раз в `__init__`-порядке: каждый элемент —
        (виджет, свойство, роль палитры). Карточки примеров и
        статусная строка перекрашиваются отдельно (их цвета зависят
        от selection/hover и тостов).
        """
        pal = self._palette
        # Крупные поверхности.
        self.main_frame.configure(fg_color=pal["bg_app"])
        self.sidebar_frame.configure(fg_color=pal["panel"])
        self.content_frame.configure(fg_color=pal["panel"])
        # Поля и терминал.
        self.search_entry.configure(
            fg_color=pal["input"],
            border_color=pal["border"],
            text_color=pal["text"],
            placeholder_text_color=pal["text_dim2"],
        )
        self.output_text.configure(
            fg_color=pal["term_bg"],
            text_color=pal["term_fg"],
            border_color=pal["border"],
        )
        # Карточки метрик и секция задач.
        for card in (
            self.metric_card_registry,
            self.metric_card_runs,
            self.metric_card_clock,
            self.metric_card_status,
            self.tasks_frame,
        ):
            card.configure(fg_color=pal["card"], border_color=pal["border"])
        # «Карточные» кнопки.
        for button in (
            self.clear_button,
            self.copy_button,
            *self.task_buttons,
            *self.demo_buttons.values(),
        ):
            button.configure(
                fg_color=pal["card"],
                hover_color=pal["card_hover"],
                border_color=pal["border"],
                text_color=pal["text"],
            )
        # Дорожки прогрессбаров.
        self.progressbar.configure(fg_color=pal["track"])
        for bar in self.task_bars:
            bar.configure(fg_color=pal["track"])
        # Сегмент темы и меню акцента.
        self.theme_segmented.configure(
            fg_color=pal["card"],
            unselected_color=pal["track"],
            unselected_hover_color=pal["card_hover"],
            text_color=pal["text"],
        )
        self.accent_menu.configure(
            fg_color=pal["card"],
            button_color=pal["border"],
            button_hover_color=pal["border_hover"],
            text_color=pal["text"],
            dropdown_fg_color=pal["card"],
            dropdown_hover_color=pal["card_hover"],
            dropdown_text_color=pal["text"],
        )
        # Тексты: яркие, обычные, приглушённые, призрачные.
        self.example_title.configure(text_color=pal["text_bright"])
        self.example_desc.configure(text_color=pal["text_dim"])
        self.theme_label = self.builder.get_object("theme_label", self.window)
        self.accent_label = self.builder.get_object("accent_label", self.window)
        self.tasks_title = self.builder.get_object("tasks_title", self.window)
        self.speed_label = self.builder.get_object("speed_label", self.window)
        for label in (
            self.theme_label,
            self.accent_label,
            self.speed_label,
        ):
            label.configure(text_color=pal["text_dim"])
        for label_id in ("task_name_1", "task_name_2", "task_name_3"):
            label = self.builder.get_object(label_id, self.window)
            label.configure(text_color=pal["text_dim"])
        for metric_label_id in (
            "metric_registry_label",
            "metric_runs_label",
            "metric_clock_label",
            "metric_status_label",
        ):
            label = self.builder.get_object(metric_label_id, self.window)
            label.configure(text_color=pal["text_dim"])
        self.metric_status_value.configure(text_color=pal["text"])
        self.search_counter.configure(text_color=pal["text_dim2"])
        self.sidebar_footer.configure(text_color=pal["text_ghost"])
        self.sidebar_badge.configure(
            fg_color=pal["card"], text_color=pal["text_dim"]
        )
        self.sidebar_title.configure(text_color=self._accent)
        self.speed_value.configure(text_color=self._accent)
        # Свитчи.
        for switch in (self.clear_before_run_switch, self.autoscroll_switch):
            switch.configure(
                text_color=pal["text"],
                fg_color=pal["track"],
                progress_color=self._accent,
                button_color=self._accent,
                button_hover_color=self._accent_hover,
            )
        # Статусная строка (базовый цвет).
        if self._toast_after_id is None:
            self.status_label.configure(text_color=pal["text_dim2"])

    def _on_accent_changed(self, value: str) -> None:
        """OptionMenu «Акцент»: перекрасить акцентные элементы."""
        self._apply_accent(value)
        self._toast(f"Акцент: {value}")

    def _apply_accent(self, name: str, *, toast: bool = True) -> None:
        """Применить акцентную палитру `name` к акцентным виджетам.

        Перекрашиваются: кнопка запуска, FAB, основной прогрессбар,
        слайдер, сегмент темы, свитчи, заголовок сайдбара, значение
        скорости. Цвета задач не трогаются — они различают задачи.
        """
        if name not in _ACCENTS:
            return
        self._accent_name = name
        self._accent, self._accent_hover = _ACCENTS[name]

        self.run_button.configure(
            fg_color=self._accent,
            hover_color=self._accent_hover,
            text_color=self._palette["on_accent"],
        )
        if hasattr(self, "fab"):
            self.fab.configure(
                fg_color=self._accent,
                hover_color=self._accent_hover,
                text_color=self._palette["on_accent"],
            )
        self.progressbar.configure(progress_color=self._accent)
        self.speed_slider.configure(
            progress_color=self._accent,
            button_color=self._accent,
            button_hover_color=self._accent_hover,
        )
        self.theme_segmented.configure(
            selected_color=self._accent,
            selected_hover_color=self._accent_hover,
        )
        self.sidebar_title.configure(text_color=self._accent)
        self.speed_value.configure(text_color=self._accent)
        for switch in (self.clear_before_run_switch, self.autoscroll_switch):
            switch.configure(
                progress_color=self._accent,
                button_color=self._accent,
                button_hover_color=self._accent_hover,
            )
        if toast:
            self._toast(f"Акцент: {name}")

    # ----------------------------------------------------------------
    # Демо-сценарии
    # ----------------------------------------------------------------
    def _on_demo_toast(self) -> None:
        """Кнопка «Тост»: временное сообщение в статусной строке."""
        self._toast("Привет! Это тост 👋")

    def _on_demo_wave(self) -> None:
        """Кнопка «Волна»: поочерёдная подсветка демо-кнопок слева направо."""
        buttons = list(self.demo_buttons.values())
        for index, button in enumerate(buttons):
            delay = index * 70

            def flash(b: ctk.CTkButton = button) -> None:
                def back() -> None:
                    self._animate(b, "fg_color", self._palette["card"], 220)

                self._animate(
                    b,
                    "fg_color",
                    self._accent_hover,
                    140,
                    on_done=back,
                )

            self.window.after(delay, flash)

    def _on_demo_flash(self) -> None:
        """Кнопка «Вспышка»: стаггерная подсветка бордеров карточек метрик."""
        cards = (
            self.metric_card_registry,
            self.metric_card_runs,
            self.metric_card_clock,
            self.metric_card_status,
        )
        for index, card in enumerate(cards):
            delay = index * 60

            def flash(c: ctk.CTkFrame = card) -> None:
                def back() -> None:
                    self._animate(c, "border_color", self._palette["border"], 260)

                self._animate(
                    c,
                    "border_color",
                    self._accent_hover,
                    140,
                    on_done=back,
                )

            self.window.after(delay, flash)

    def _on_demo_reset(self) -> None:
        """Кнопка «Сброс»: остановить задачи, очистить вывод и счётчики."""
        for idx, state in enumerate(self._task_states):
            after_id = state["after_id"]
            if after_id is not None:
                try:
                    self.window.after_cancel(str(after_id))
                except Exception:
                    pass
            state["running"] = False
            state["value"] = 0.0
            state["after_id"] = None
            self.task_buttons[idx].configure(state="normal")
            self.task_bars[idx].set(0)
            self.task_pcts[idx].configure(text="0%")
        self._task_chain.clear()
        self.progressbar.stop()
        self.progressbar.set(0)
        self._clear_output()
        self._runs_count = 0
        self.metric_runs_value.configure(text="0")
        self._set_status(_STATUS_RESET)

    def _on_demo_test(self) -> None:
        """Кнопка «Тест»: запустить все три задачи цепочкой."""
        if any(state["running"] for state in self._task_states):
            self._toast("Задачи уже выполняются")
            return
        self._task_chain = [1, 2]
        self._start_task(0)
        self._toast("Тест: цепочка из 3 задач")

    # ----------------------------------------------------------------
    # Симуляция задач
    # ----------------------------------------------------------------
    def _on_speed_changed(self, value: float) -> None:
        """Слайдер скорости: 1..10, отражается в подписи «Nx»."""
        speed = int(round(float(value)))
        speed = max(1, min(10, speed))
        self._speed = speed
        self.speed_value.configure(text=f"{speed}x")

    def _start_task(self, index: int) -> None:
        """Запустить симуляцию задачи `index` (0..2).

        Анимация прогрессбара — пошаговая через `after`: шаг каждые
        30 мс, приращение зависит от слайдера скорости. По завершении
        кнопка разблокируется, в терминал пишется итог, и, если есть
        очередь цепочки («Тест»), стартует следующая задача.
        """
        state = self._task_states[index]
        if state["running"]:
            return
        state["running"] = True
        state["value"] = 0.0
        self.task_buttons[index].configure(state="disabled")
        self._bump_runs()
        title = _TASK_TITLES[index]
        self._append_output(f"▶ Задача запущена: {title}\n", tag=_TAG_HDR)
        # Запоминаем базовый статус, чтобы после завершения задачи
        # вернуть его (например, «Выбран: ...»), а не «Готово».
        if not self._status_text.startswith("Задача: "):
            self._status_before_task: str = self._status_text
        self._set_status(f"Задача: {title}")
        self._task_step(index)

    def _task_step(self, index: int) -> None:
        """Один шаг анимации задачи: приращение бара и процента."""
        if self._closing:
            return
        state = self._task_states[index]
        if not state["running"]:
            return
        # Приращение за шаг: базовая скорость 5x ≈ полный бар за ~2 с.
        step = 0.015 * (self._speed / 5.0)
        value = float(state["value"]) + step
        if value >= 1.0:
            value = 1.0
        state["value"] = value
        self.task_bars[index].set(value)
        self.task_pcts[index].configure(text=f"{round(value * 100)}%")
        if value < 1.0:
            state["after_id"] = self.window.after(
                30, lambda: self._task_step(index)
            )
        else:
            self._finish_task(index)

    def _finish_task(self, index: int) -> None:
        """Завершение задачи: UI, лог, цепочка «Тест»."""
        state = self._task_states[index]
        state["running"] = False
        state["after_id"] = None
        self.task_buttons[index].configure(state="normal")
        title = _TASK_TITLES[index]
        self._append_output(f"✔ Задача завершена: {title} (100%)\n", tag=_TAG_HDR)
        self._set_metric_status(_STATUS_DONE)
        if self._status_text.startswith("Задача: "):
            self._set_status(getattr(self, "_status_before_task", _STATUS_READY))
        if self._task_chain:
            nxt = self._task_chain.pop(0)
            self.window.after(250, lambda: self._start_task(nxt))

    def _bump_runs(self) -> None:
        """Инкремент счётчика запусков (примеры и симуляции задач)."""
        self._runs_count += 1
        self.metric_runs_value.configure(text=str(self._runs_count))

    # ----------------------------------------------------------------
    # Вводная анимация карточек
    # ----------------------------------------------------------------
    def _intro_cards(self) -> None:
        """Появление карточек: поочерёдный fade от фона панели к карточке.

        Лёгкий «влёт» контента при старте: каждая карточка начинает
        с цвета панели и плавно проявляется к своему цвету; стаггер —
        50 мс между карточками.
        """
        for index, (example_id, card) in enumerate(self._cards.items()):
            self._apply(card, "fg_color", self._palette["panel"])

            def reveal(c: ctk.CTkFrame = card, eid: str = example_id) -> None:
                self._animate(c, "fg_color", self._palette["card"], 260)

            self.window.after(120 + index * 50, reveal)

    # ----------------------------------------------------------------
    # Терминал: теги и вывод
    # ----------------------------------------------------------------
    def _configure_terminal_tags(self) -> None:
        """Настроить теги подсветки терминала под активную палитру."""
        try:
            self.output_text.tag_config(
                _TAG_HDR, foreground=self._accent
            )
            self.output_text.tag_config(
                _TAG_ERR, foreground="#ff6b9d"
            )
        except Exception:
            # Если теги недоступны — вывод остаётся монохромным.
            pass

    def _append_output(self, text: str, tag: str | None = None) -> None:
        """Дописать текст в конец `output_text`. Только из главного потока.

        В конце — автопрокрутка к последней строке, подчиняющаяся
        свитчу `autoscroll_switch`. Если передан тег — строка
        подсвечивается (hdr/err).
        """
        self.output_text.configure(state="normal")
        if tag is not None:
            self.output_text.insert("end", text, tag)
        else:
            self.output_text.insert("end", text)
        if self._autoscroll_enabled():
            self.output_text.see("end")

    def _autoscroll_enabled(self) -> bool:
        """Сообщить, включён ли свитч автопрокрутки.

        `CTkSwitch.get()` возвращает 1/0 в большинстве версий
        CustomTkinter; при любом сбое считаем свитч выключенным.
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

        Возвращает `False`, если в `output_text` пусто (тогда не
        трогаем буфер).
        """
        content = self.output_text.get("1.0", "end-1c")
        if not content:
            return False
        self.window.clipboard_clear()
        self.window.clipboard_append(content)
        # `update_idletasks` форсирует обработку событий буфера обмена
        # до того, как окно/процесс закроется.
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
        """Клик по карточке: выбрать пример и обновить шапку."""
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
        """Курсор вошёл в карточку: применяем hover (анимированный)."""
        self._hover_card_id = example_id
        self._apply_card_appearance(example_id)

    def _on_card_leave(self, example_id: str) -> None:
        """Курсор покинул карточку: снимаем hover.

        Если мышь «переехала» на дочерний label той же карточки,
        Leave на родителе срабатывает раньше, чем Enter на label'е —
        актуальный hover_id обновится в `_on_card_enter` следующим
        тиком, и финальный цвет будет корректным.
        """
        if self._hover_card_id == example_id:
            self._hover_card_id = None
        self._apply_card_appearance(example_id)

    def _apply_card_appearance(self, example_id: str) -> None:
        """Пересчитать цвета карточки по (selected, hover) — с анимацией.

        Приоритет: selected > hover > default.
        - selected: бордер — акцент, фон — `card_selected`.
        - hover: фон — `card_hover`.
        - default: базовые `card`/`border`.
        Переходы анимируются (160 мс), поэтому карточки «парят».
        """
        if example_id not in self._cards:
            return
        card = self._cards[example_id]
        is_selected = example_id == self._selected_example_id
        is_hovered = example_id == self._hover_card_id

        if is_selected:
            fg = self._palette["card_selected"]
            border = self._accent
        elif is_hovered:
            fg = self._palette["card_hover"]
            border = self._palette["border_hover"]
        else:
            fg = self._palette["card"]
            border = self._palette["border"]

        self._animate(card, "fg_color", fg)
        self._animate(card, "border_color", border)

    # ----------------------------------------------------------------
    # Фильтрация карточек поиском
    # ----------------------------------------------------------------
    def _on_search_changed(self, *_args: object) -> None:
        """Обработчик изменения `search_entry`: фильтрует карточки.

        Фильтрация по подстроке (case-insensitive) по title или
        description примера. Видимость переключаем через
        `grid_remove()` / `grid()` — настройки grid сохраняются.

        Также обновляет `search_counter` в формате «Найдено: N из 5».
        """
        new_text = self._search_var.get()
        if new_text == self._search_text:
            # `trace_add` иногда срабатывает на идентичное значение.
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
                desc_label = self._card_labels[example_id][1]
                description = desc_label.cget("text").lower()
                visible = (query in title) or (query in description)
            if visible:
                visible_count += 1
                card.grid()
            else:
                card.grid_remove()

        self.search_counter.configure(
            text=f"Найдено: {visible_count} из {self._total_examples}"
        )

    # ----------------------------------------------------------------
    # Запуск примера в потоке
    # ----------------------------------------------------------------
    def _set_metric_status(self, text: str, *, error: bool = False) -> None:
        """Обновить значение метрики «Статус» и, опционально, её цвет."""
        color = "#ff6b9d" if error else self._palette["text"]
        self.metric_status_value.configure(text=text, text_color=color)

    def _set_running(self, running: bool) -> None:
        """Переключить блокировку UI на время выполнения примера.

        Блокируем кнопку запуска, FAB, поле поиска и клики по
        карточкам, чтобы нельзя было сменить выбор посреди прогона.
        """
        if running:
            self.run_button.configure(
                state="disabled",
                text=_BUTTON_RUN_RUNNING,
            )
            # FAB создаётся после первого `_set_running(False)` в
            # `__init__`, поэтому здесь защита по hasattr.
            if hasattr(self, "fab"):
                self.fab.configure(state="disabled")
            self.search_entry.configure(state="disabled")
            self._set_cards_bind_enabled(False)
        else:
            self.run_button.configure(
                state="normal",
                text=_BUTTON_RUN_TEXT,
            )
            if hasattr(self, "fab"):
                self.fab.configure(state="normal")
            self.search_entry.configure(state="normal")
            self._set_cards_bind_enabled(True)

    def _set_cards_bind_enabled(self, enabled: bool) -> None:
        """Включить/выключить bind'ы карточек на время выполнения примера."""
        for example_id, card in self._cards.items():
            labels = self._card_labels[example_id]
            for widget in (card, *labels):
                if enabled:
                    self._bind_card_events(card, example_id, labels)
                else:
                    for sequence in ("<Button-1>", "<Enter>", "<Leave>"):
                        widget.unbind(sequence)

    def _on_run_clicked(self) -> None:
        """Кнопка «Запустить»: проверить выбор и стартовать воркер.

        Уважает свитч `clear_before_run_switch`: если он включён —
        `output_text` очищается перед запуском.
        """
        if self._worker is not None:
            return

        example_id = self._selected_example_id
        if example_id is None:
            self._toast(_STATUS_NO_SELECTION)
            self._append_output(
                "⚠ Выберите пример в списке слева и повторите.\n",
                tag=_TAG_ERR,
            )
            return

        if self._clear_before_run_enabled():
            self._clear_output()
        self._start_example(example_id)

    def _clear_before_run_enabled(self) -> bool:
        """Сообщить, включён ли свитч «Очистка перед запуском»."""
        try:
            value = self.clear_before_run_switch.get()
        except Exception:
            return False
        try:
            return int(value) == 1
        except (TypeError, ValueError):
            return bool(value)

    def _start_example(self, example_id: str) -> None:
        """Подготовить UI и запустить пример `example_id` в потоке.

        1. Проверить, что воркера нет (идемпотентность).
        2. Заблокировать UI, при необходимости очистить вывод.
        3. Выставить статус «Выполняется...» и обновить метрики.
        4. Запустить `progressbar.start()` (indeterminate-режим).
        5. Создать daemon-поток и положить его в `self._worker`.
        6. Запланировать `_poll_queue` через `self.window.after`.
        """
        if self._worker is not None:
            return

        self._set_running(True)
        if not self._clear_before_run_enabled():
            self._clear_output()
        title = self._id_to_title.get(example_id, example_id)
        self._set_status(_STATUS_RUNNING)
        self._set_metric_status(_STATUS_RUNNING)
        self._bump_runs()
        # CTk 6.0.0: `CTkProgressBar.start()` не принимает аргументов.
        self.progressbar.start()

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

        self._append_output(
            f"=== Запуск: {title} ({example_id}) ===\n", tag=_TAG_HDR
        )

        self.window.after(_QUEUE_POLL_MS, self._poll_queue)

    def _run_in_worker(self, example_id: str) -> None:
        """Тело фонового потока: вызвать `run_example` и положить результат.

        Исключения примера не подавляются: traceback уходит в очередь
        как терминальное сообщение `"error"`.
        """
        try:
            result = run_example(example_id)
        except Exception:
            self._queue.put(("error", traceback.format_exc()))
            return
        self._queue.put(("done", result))

    def _poll_queue(self) -> None:
        """Главный поток: забрать из очереди и обновить UI.

        - Пока воркер жив или в очереди что-то лежит — забираем
          `get_nowait`, обрабатываем каждое сообщение.
        - Терминальное сообщение (`done`/`error`) закрывает прогон:
          останавливаем прогрессбар, разблокируем UI, обновляем
          статусы и метрики.
        - Иначе планируем следующий опрос, пока есть работа.
        """
        terminal: tuple[str, object] | None = None
        try:
            while True:
                kind, payload = self._queue.get_nowait()
                if kind == "done":
                    self._append_output(str(payload))
                    terminal = (kind, payload)
                elif kind == "error":
                    self._append_output(
                        f"[ОШИБКА]\n{payload}\n", tag=_TAG_ERR
                    )
                    terminal = (kind, payload)
                else:
                    import logging
                    logging.getLogger(__name__).warning(
                        "Unknown queue message kind: %r", kind
                    )
                    terminal = (kind, payload)
        except queue.Empty:
            pass

        if terminal is not None:
            self.progressbar.stop()
            self._set_running(False)
            kind, _payload = terminal
            if kind == "done":
                self._set_status(_STATUS_DONE)
                self._set_metric_status(_STATUS_DONE)
            else:
                self._set_status(_STATUS_ERROR)
                self._set_metric_status(_STATUS_ERROR, error=True)
            self._worker = None
            return

        if self._worker is not None or not self._queue.empty():
            self.window.after(_QUEUE_POLL_MS, self._poll_queue)
        else:
            self.progressbar.stop()
            self._set_running(False)

    # ----------------------------------------------------------------
    # Кнопки: очистка, копирование, закрытие
    # ----------------------------------------------------------------
    def _on_clear_clicked(self) -> None:
        """Кнопка «Очистить»: стереть `output_text` и сбросить статус."""
        self._clear_output()
        self._set_status(_STATUS_READY)

    def _on_copy_clicked(self) -> None:
        """Кнопка «Копировать»: перенести `output_text` в clipboard."""
        if self._copy_output_to_clipboard():
            self._toast(_STATUS_COPIED)
        else:
            self._toast(_STATUS_COPIED_EMPTY)

    def _on_close(self) -> None:
        """Обработчик закрытия окна (крестик): корректно выйти из mainloop.

        `self._worker` — daemon-поток; при выходе из процесса он и так
        умрёт. Все after-цепочки проверяют `self._closing` и не
        перезапланируются.
        """
        self._closing = True
        self.window.quit()
