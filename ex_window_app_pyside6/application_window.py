"""Окно примера на PySide6: два поля ввода, две кнопки и метка результата.

Модуль только описывает класс окна. Импорт модуля не создаёт ``QApplication``
и не создаёт виджетов — это делает вызывающий код (точка входа).
"""

from __future__ import annotations

from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

# Стартовый и «пустой» тексты метки результата.
RESULT_PLACEHOLDER = "—"
RESULT_EMPTY_INPUT = "Введите имя и сообщение"


class ApplicationWindow(QWidget):
    """Окно с двумя полями ввода и двумя кнопками.

    Поля и кнопки получают objectName из контракта фазы: на эти имена
    опираются checkpoint и проверки.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("PySide6 — пример окна")
        self.setObjectName("application_window")
        self._build_layout()
        # Сигналы привязываются после создания виджетов в _build_layout.
        self.show_button.clicked.connect(self._on_show_clicked)
        self.clear_button.clicked.connect(self._on_clear_clicked)

    def _build_layout(self) -> None:
        """Собирает вертикальную разметку окна из подписей, полей и кнопок."""
        layout = QVBoxLayout(self)

        # Поле «Имя».
        name_label = QLabel("Имя", self)
        self.name_input = QLineEdit(self)
        self.name_input.setObjectName("name_input")
        layout.addWidget(name_label)
        layout.addWidget(self.name_input)

        # Поле «Сообщение».
        message_label = QLabel("Сообщение", self)
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