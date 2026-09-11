"""Окно примера на PySide6: поля ввода, кнопки и демонстрационные элементы.

Модуль только описывает класс окна. Импорт модуля не создаёт ``QApplication``
и не создаёт виджетов — это делает вызывающий код (точка входа).
"""

from __future__ import annotations

from string import Template

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPalette, QShowEvent
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QProgressBar,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)

# Стартовый и «пустой» тексты метки результата.
RESULT_PLACEHOLDER = "—"
RESULT_EMPTY_INPUT = "Введите имя и сообщение"

# Палитры тем оформления: один набор цветов на всё окно.
# Ключи словаря — названия тем, они же показываются в QComboBox.
THEME_PALETTES: dict[str, dict[str, str]] = {
    "Малиновый": {
        "window_start": "#fdf2f8",
        "window_end": "#fce7f3",
        "text": "#1f2937",
        "title": "#be185d",
        "label": "#831843",
        "field_bg": "#ffffff",
        "field_border": "#f9a8d4",
        "field_focus": "#db2777",
        "field_text": "#111827",
        "placeholder": "#9d174d",
        "button": "#db2777",
        "button_text": "#ffffff",
        "button_hover": "#be185d",
        "clear_button": "#f472b6",
        "clear_button_hover": "#ec4899",
        "slider_groove": "#fbcfe8",
        "slider_handle": "#db2777",
        "progress_bg": "#fce7f3",
        "progress_start": "#db2777",
        "progress_end": "#f59e0b",
        "progress_text": "#831843",
        "checkbox_border": "#f9a8d4",
        "checkbox_checked": "#db2777",
        "combo_bg": "#ffffff",
        "combo_border": "#f9a8d4",
        "combo_text": "#831843",
        "combo_selection_bg": "#fce7f3",
        "combo_selection_text": "#831843",
        "result_bg": "#ffffff",
        "result_border": "#f9a8d4",
        "result_text": "#be185d",
    },
    "Изумрудный": {
        "window_start": "#ecfdf5",
        "window_end": "#d1fae5",
        "text": "#1f2937",
        "title": "#047857",
        "label": "#064e3b",
        "field_bg": "#ffffff",
        "field_border": "#a7f3d0",
        "field_focus": "#059669",
        "field_text": "#111827",
        "placeholder": "#065f46",
        "button": "#059669",
        "button_text": "#ffffff",
        "button_hover": "#047857",
        "clear_button": "#34d399",
        "clear_button_hover": "#10b981",
        "slider_groove": "#a7f3d0",
        "slider_handle": "#059669",
        "progress_bg": "#d1fae5",
        "progress_start": "#059669",
        "progress_end": "#0ea5e9",
        "progress_text": "#064e3b",
        "checkbox_border": "#a7f3d0",
        "checkbox_checked": "#059669",
        "combo_bg": "#ffffff",
        "combo_border": "#a7f3d0",
        "combo_text": "#064e3b",
        "combo_selection_bg": "#d1fae5",
        "combo_selection_text": "#064e3b",
        "result_bg": "#ffffff",
        "result_border": "#a7f3d0",
        "result_text": "#047857",
    },
    "Индиго": {
        "window_start": "#eef2ff",
        "window_end": "#e0e7ff",
        "text": "#1f2937",
        "title": "#4338ca",
        "label": "#3730a3",
        "field_bg": "#ffffff",
        "field_border": "#c7d2fe",
        "field_focus": "#6366f1",
        "field_text": "#111827",
        "placeholder": "#3730a3",
        "button": "#6366f1",
        "button_text": "#ffffff",
        "button_hover": "#4f46e5",
        "clear_button": "#818cf8",
        "clear_button_hover": "#6366f1",
        "slider_groove": "#c7d2fe",
        "slider_handle": "#6366f1",
        "progress_bg": "#e0e7ff",
        "progress_start": "#6366f1",
        "progress_end": "#a855f7",
        "progress_text": "#3730a3",
        "checkbox_border": "#c7d2fe",
        "checkbox_checked": "#6366f1",
        "combo_bg": "#ffffff",
        "combo_border": "#c7d2fe",
        "combo_text": "#3730a3",
        "combo_selection_bg": "#e0e7ff",
        "combo_selection_text": "#3730a3",
        "result_bg": "#ffffff",
        "result_border": "#c7d2fe",
        "result_text": "#4338ca",
    },
}

DEFAULT_THEME = "Малиновый"

# Обратная совместимость: прежний контракт «тема -> цвет метки результата».
THEME_COLORS = {
    name: palette["result_text"] for name, palette in THEME_PALETTES.items()
}


def _palette_for(theme: str) -> dict[str, str]:
    """Возвращает палитру темы или палитру по умолчанию."""
    return THEME_PALETTES.get(theme, THEME_PALETTES[DEFAULT_THEME])


# Шаблон QSS: цвета подставляются из палитры выбранной темы.
_STYLE_TEMPLATE = Template("""
QWidget#application_window {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 $window_start, stop:1 $window_end);
    font-family: "DejaVu Sans", "Segoe UI", sans-serif;
    font-size: 14px;
    color: $text;
}
QLabel#title_label {
    font-size: 20px;
    font-weight: 700;
    color: $title;
    padding: 4px 0 8px 0;
}
QLabel#name_label, QLabel#message_label, QLabel#volume_label,
QLabel#mode_label, QLabel#theme_label, QLabel#slider_value_label {
    font-weight: 600;
    color: $label;
}
QLineEdit {
    background: $field_bg;
    border: 2px solid $field_border;
    border-radius: 10px;
    padding: 6px 10px;
    color: $field_text;
    selection-background-color: $button;
    selection-color: $field_bg;
}
QLineEdit:focus {
    border: 2px solid $field_focus;
}
QPushButton {
    background: $button;
    color: $button_text;
    border: none;
    border-radius: 12px;
    padding: 8px 18px;
    font-weight: 600;
}
QPushButton:hover {
    background: $button_hover;
}
QPushButton#clear_button {
    background: $clear_button;
}
QPushButton#clear_button:hover {
    background: $clear_button_hover;
}
QSlider::groove:horizontal {
    height: 8px;
    background: $slider_groove;
    border-radius: 4px;
}
QSlider::handle:horizontal {
    background: $slider_handle;
    width: 18px;
    margin: -6px 0;
    border-radius: 9px;
}
QProgressBar {
    background: $progress_bg;
    border: none;
    border-radius: 10px;
    min-height: 20px;
    text-align: center;
    color: $progress_text;
    font-weight: 600;
}
QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 $progress_start, stop:1 $progress_end);
    border-radius: 10px;
}
QCheckBox {
    spacing: 8px;
    font-weight: 600;
    color: $label;
}
QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border-radius: 6px;
    border: 2px solid $checkbox_border;
    background: $field_bg;
}
QCheckBox::indicator:checked {
    background: $checkbox_checked;
    border: 2px solid $checkbox_checked;
}
QComboBox {
    background: $combo_bg;
    border: 2px solid $combo_border;
    border-radius: 10px;
    padding: 6px 10px;
    font-weight: 600;
    color: $combo_text;
}
QComboBox:focus {
    border: 2px solid $field_focus;
}
QComboBox QAbstractItemView {
    background: $combo_bg;
    color: $combo_text;
    selection-background-color: $combo_selection_bg;
    selection-color: $combo_selection_text;
    border-radius: 8px;
}
QLabel#result_label {
    background: $result_bg;
    border: 2px dashed $result_border;
    border-radius: 12px;
    padding: 10px;
    color: $result_text;
    font-weight: 600;
}
""")


def _build_style_sheet(palette: dict[str, str]) -> str:
    """Собирает таблицу стилей окна из палитры выбранной темы."""
    return _STYLE_TEMPLATE.substitute(palette)


class ApplicationWindow(QWidget):
    """Окно с полями ввода, кнопками и демонстрационными элементами.

    Поля, кнопки и демонстрационные виджеты получают objectName из контракта
    фазы: на эти имена опираются checkpoint и проверки.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("PySide6 — пример окна")
        self.setObjectName("application_window")
        self._build_layout()
        # Сигналы привязываются после создания виджетов в _build_layout.
        self.show_button.clicked.connect(self._on_show_clicked)
        self.clear_button.clicked.connect(self._on_clear_clicked)
        self.volume_slider.valueChanged.connect(self._on_volume_changed)
        self.mode_checkbox.toggled.connect(self._on_mode_toggled)
        self.theme_combo.currentTextChanged.connect(self._on_theme_changed)

    def showEvent(self, event: QShowEvent) -> None:
        """Повторно применяет тему после показа окна.

        Qt при первой полировке сбрасывает роль ``PlaceholderText`` у полей,
        поэтому палитру нужно задать ещё раз, когда окно уже показано.
        """
        super().showEvent(event)
        self._apply_theme(self.theme_combo.currentText())

    def _build_layout(self) -> None:
        """Собирает вертикальную разметку окна из подписей, полей и кнопок."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)

        # Заголовок окна.
        title_label = QLabel("Демонстрационное окно", self)
        title_label.setObjectName("title_label")
        layout.addWidget(title_label)

        # Поле «Имя».
        name_label = QLabel("Имя", self)
        name_label.setObjectName("name_label")
        self.name_input = QLineEdit(self)
        self.name_input.setObjectName("name_input")
        layout.addWidget(name_label)
        layout.addWidget(self.name_input)

        # Поле «Сообщение».
        message_label = QLabel("Сообщение", self)
        message_label.setObjectName("message_label")
        self.message_input = QLineEdit(self)
        self.message_input.setObjectName("message_input")
        layout.addWidget(message_label)
        layout.addWidget(self.message_input)

        # Строка с двумя кнопками.
        buttons_layout = QHBoxLayout()
        self.show_button = QPushButton("Показать", self)
        self.show_button.setObjectName("show_button")
        self.clear_button = QPushButton("Очистить", self)
        self.clear_button.setObjectName("clear_button")
        buttons_layout.addWidget(self.show_button)
        buttons_layout.addWidget(self.clear_button)
        layout.addLayout(buttons_layout)

        # Метка результата.
        self.result_label = QLabel(RESULT_PLACEHOLDER, self)
        self.result_label.setObjectName("result_label")
        layout.addWidget(self.result_label)

        # Ползунок «Громкость» с отображением значения.
        volume_layout = QHBoxLayout()
        volume_label = QLabel("Громкость", self)
        volume_label.setObjectName("volume_label")
        self.volume_slider = QSlider(Qt.Orientation.Horizontal, self)
        self.volume_slider.setObjectName("volume_slider")
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(40)
        self.slider_value_label = QLabel("40%", self)
        self.slider_value_label.setObjectName("slider_value_label")
        volume_layout.addWidget(volume_label)
        volume_layout.addWidget(self.volume_slider)
        volume_layout.addWidget(self.slider_value_label)
        layout.addLayout(volume_layout)

        # Флажок «Яркий режим» и выбор темы оформления.
        options_layout = QHBoxLayout()
        self.mode_checkbox = QCheckBox("Яркий режим", self)
        self.mode_checkbox.setObjectName("mode_checkbox")
        self.mode_checkbox.setChecked(True)
        theme_label = QLabel("Тема", self)
        theme_label.setObjectName("theme_label")
        self.theme_combo = QComboBox(self)
        self.theme_combo.setObjectName("theme_combo")
        self.theme_combo.addItems(list(THEME_COLORS))
        options_layout.addWidget(self.mode_checkbox)
        options_layout.addWidget(theme_label)
        options_layout.addWidget(self.theme_combo)
        layout.addLayout(options_layout)

        # Индикатор прогресса, связанный с ползунком.
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setObjectName("progress_bar")
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(self.volume_slider.value())
        layout.addWidget(self.progress_bar)

        # Применяем стартовую тему к метке результата.
        self._apply_theme(self.theme_combo.currentText())

    def _on_show_clicked(self) -> None:
        """Показывает в метке введённые имя и сообщение."""
        name = self.name_input.text()
        message = self.message_input.text()
        if not name and not message:
            self.result_label.setText(RESULT_EMPTY_INPUT)
            return
        self.result_label.setText(f"{name}: {message}")

    def _on_clear_clicked(self) -> None:
        """Очищает оба поля ввода и возвращает метку в стартовое состояние."""
        self.name_input.clear()
        self.message_input.clear()
        self.result_label.setText(RESULT_PLACEHOLDER)

    def _on_volume_changed(self, value: int) -> None:
        """Синхронизирует подпись и индикатор прогресса с ползунком."""
        self.slider_value_label.setText(f"{value}%")
        self.progress_bar.setValue(value)

    def _on_mode_toggled(self, checked: bool) -> None:
        """Включает и выключает показ текста на индикаторе прогресса."""
        self.progress_bar.setTextVisible(checked)

    def _on_theme_changed(self, theme: str) -> None:
        """Применяет палитру выбранной темы ко всему окну."""
        self._apply_theme(theme)

    def _apply_theme(self, theme: str) -> None:
        """Применяет палитру выбранной темы ко всему окну."""
        palette = _palette_for(theme)
        self.setStyleSheet(_build_style_sheet(palette))
        window_palette = self.palette()
        window_palette.setColor(QPalette.ColorRole.WindowText, QColor(palette["text"]))
        window_palette.setColor(QPalette.ColorRole.Text, QColor(palette["field_text"]))
        window_palette.setColor(QPalette.ColorRole.Base, QColor(palette["field_bg"]))
        self.setPalette(window_palette)
        # Плейсхолдер задаётся только через палитру: QSS его не поддерживает.
        field_palette = self.name_input.palette()
        field_palette.setColor(QPalette.ColorRole.Text, QColor(palette["field_text"]))
        field_palette.setColor(
            QPalette.ColorRole.PlaceholderText, QColor(palette["placeholder"])
        )
        for field in (self.name_input, self.message_input):
            field.setPalette(field_palette)