"""Реестр курируемых примеров и запуск с захватом вывода.

Модуль спроектирован так, чтобы:
- не зависеть от GUI (без импорта tkinter/ttkbootstrap/pygubu);
- работать в headless-режиме (без дисплея), потому что используется
  и smoke-проверкой, и GUI-потоком приложения.

Реестр — это `list[ExampleDescriptor]`. Каждый дескриптор описывает
один учебный пример: стабильный id, человекочитаемое название и
вызываемую функцию (без аргументов или с аргументом-маркером).

`run_example(name)` запускает пример в текущем потоке, временно
подменяя `sys.stdout`/`sys.stderr` на `io.StringIO` и подключая
`logging.handlers.QueueHandler` к корневому логгеру. Возвращает
объединённую строку stdout + stderr + отформатированных записей лога.
Исключения из примера не подавляются: они пробрасываются, но
stdout/stderr/handler восстанавливаются в блоке `finally`.

Замечание о порядке инициализации: модули примеров импортируются на
уровне модуля (eager). Это нужно, чтобы при первом импорте каждого
примера его логгер (`ConfigLogger.get_logger`) был сконфигурирован
один раз, и `run_example` не вызывал побочный `dictConfig`/`basicConfig`
уже после установки нашего `QueueHandler`. Без этого побочный
`basicConfig(handlers=[])` мутирует `LogRecord.msg` в момент
перенаправления `sys.stderr`, и в вывод попадают строки с
уже отформатированным префиксом.
"""

from __future__ import annotations

import contextlib
import dataclasses
import io
import logging
import logging.handlers
import queue
import sys
from collections.abc import Callable
from typing import Any, Final


# ------------------------------------------------------------------------
# Eager-импорт модулей примеров
# ------------------------------------------------------------------------
# Импортируем заранее, чтобы `ConfigLogger` в каждом из них отработал
# ровно один раз при загрузке runner'а, а не во время захвата вывода.
# Все модули — обычный Python-код проекта (никакого GUI), и они не
# выполняют побочных действий при импорте, кроме инициализации логгера.
from ex_async_simple.main_async_simple import run_simple_demo  # noqa: E402, F401
from ex_code_war.main_code_war import code_war_1  # noqa: E402, F401
from ex_file_zip.main_file import run_file_zip  # noqa: E402, F401
from ex_metaclass.main_metaclass import main_metaclass  # noqa: E402, F401
from ex_work_process.main_work_process import run_process_demo  # noqa: E402, F401


# ------------------------------------------------------------------------
# Снимок `LogRecord` в момент попадания в очередь
# ------------------------------------------------------------------------
# Подмеченный нюанс `ConfigLogger` + `contextlib.redirect_*`:
# при активном `redirect_stdout`/`redirect_stderr` внутри импорта
# примеров запись `LogRecord.msg` иногда оказывается уже
# отформатированной строкой с префиксом (asctime/levelname/name).
# Чтобы вывод не двоился, мы делаем снимок полей записи в подклассе
# `QueueHandler` сразу в `emit()` и затем форматируем строку сами,
# опираясь на снимок, а не на потенциально мутированный record.
class _SnapshottingQueueHandler(logging.handlers.QueueHandler):  # type: ignore[misc]
    """`QueueHandler`, который делает снимок полей в `emit()`.

    Сохраняет в атрибутах записи `record._snap_*` оригинальные значения
    `msg`, `args` и `created`, чтобы последующее форматирование
    опиралось именно на них, даже если кто-то по пути мутирует
    `record.msg`/`record.message`.
    """

    def emit(self, record: logging.LogRecord) -> None:
        # Сохраняем оригинал до того, как кто-либо успеет вызвать
        # `record.getMessage()` или `Formatter.format()` (последний
        # кэширует результат в `record.message`).
        if not hasattr(record, "_snap_done"):
            record._snap_msg = record.msg
            record._snap_args = record.args
            record._snap_created = record.created
            record._snap_done = True  # type: ignore[attr-defined]
        super().emit(record)


# ------------------------------------------------------------------------
# Дескриптор примера
# ------------------------------------------------------------------------
@dataclasses.dataclass(frozen=True)
class ExampleDescriptor:
    """Описание одного учебного примера, доступного из GUI.

    Поля:
    - example_id: стабильный идентификатор (используется в реестре,
      в комбобоксе и в headless-smoke `--smoke <id>`).
    - title: человекочитаемое название, отображаемое в списке.
    - runner: вызываемая функция без аргументов. Сигнатуры функций
      из существующих примеров разные (часть принимает `w=None`,
      часть — нет), поэтому адаптация делается здесь, в `_make_runner`,
      а наружу отдаётся `Callable[[], None]`.
    """

    example_id: str
    title: str
    runner: Callable[[], None]


# ------------------------------------------------------------------------
# Адаптеры под существующие сигнатуры
# ------------------------------------------------------------------------
def _run_async_simple_demo() -> None:
    """Запуск `ex_async_simple.main_async_simple.run_simple_demo(None)`."""
    run_simple_demo(None)


def _run_code_war_1() -> None:
    """Запуск `ex_code_war.main_code_war.code_war_1(None)`."""
    code_war_1(None)


def _run_file_zip() -> None:
    """Запуск `ex_file_zip.main_file.run_file_zip(None)`."""
    run_file_zip(None)


def _run_metaclass() -> None:
    """Запуск `ex_metaclass.main_metaclass.main_metaclass(None)`."""
    main_metaclass(None)


def _run_process_demo() -> None:
    """Запуск `ex_work_process.main_work_process.run_process_demo()`.

    Функция имеет сигнатуру `run_process_demo(w=None)`, поэтому вызов
    без аргументов допустим.
    """
    run_process_demo()


# ------------------------------------------------------------------------
# Реестр
# ------------------------------------------------------------------------
_EXAMPLES: Final[list[ExampleDescriptor]] = [
    ExampleDescriptor(
        example_id="async_context_var",
        title="Async: ContextVar в задачах",
        runner=_run_async_simple_demo,
    ),
    ExampleDescriptor(
        example_id="valid_bracket",
        title="Code War: проверка скобочных последовательностей",
        runner=_run_code_war_1,
    ),
    ExampleDescriptor(
        example_id="zip_operations",
        title="ZIP: запись и чтение архивов",
        runner=_run_file_zip,
    ),
    ExampleDescriptor(
        example_id="metaclass_vars",
        title="Metaclass: переменные внутри функций",
        runner=_run_metaclass,
    ),
    ExampleDescriptor(
        example_id="multiprocessing_demo",
        title="Multiprocessing: Process / Pool / Executor",
        runner=_run_process_demo,
    ),
]


def list_examples() -> list[ExampleDescriptor]:
    """Вернуть копию реестра примеров.

    Возвращается новый список, чтобы вызывающий код не мог случайно
    мутировать внутренний реестр модуля.
    """
    return list(_EXAMPLES)


def get_example(name: str) -> ExampleDescriptor:
    """Найти дескриптор по `example_id`.

    При неизвестном имени поднимается `KeyError` с понятным сообщением
    и списком известных идентификаторов — это удобнее, чем голое
    "not found", и упрощает диагностику из GUI и smoke-проверки.
    """
    for descriptor in _EXAMPLES:
        if descriptor.example_id == name:
            return descriptor
    known = ", ".join(sorted(d.example_id for d in _EXAMPLES))
    msg = f"Unknown example id: {name!r}. Known ids: {known}"
    raise KeyError(msg)


# ------------------------------------------------------------------------
# Запуск примера с захватом вывода
# ------------------------------------------------------------------------
_LOG_DATEFMT: Final[str] = "%Y-%m-%d %H:%M:%S"


def _format_record(record: logging.LogRecord) -> str:
    """Превратить запись лога в строку на основе снимка `_snap_*`.

    Используем снимок вместо `Formatter.format(record)`, чтобы не
    зависеть от возможной мутации `record.msg`/`record.message`
    на пути между `emit` и `drain` (см. комментарий к
    `_SnapshottingQueueHandler`).
    """
    # Достаём снимок: если по какой-то причине его нет (например,
    # запись пришла из чужого QueueHandler), используем безопасные
    # fallback'и.
    msg: Any = getattr(record, "_snap_msg", record.msg)
    args: Any = getattr(record, "_snap_args", record.args)
    created: float = getattr(record, "_snap_created", record.created)

    # Применяем args → итоговое сообщение, как делает `record.getMessage()`.
    if args:
        try:
            rendered = msg % args
        except Exception:
            rendered = str(msg)
    else:
        rendered = str(msg)

    asctime: str
    # `Formatter.formatTime` использует `record.created`; временно
    # подменяем его на снимок, чтобы вывод не зависел от возможной
    # мутации `record.created` на пути между `emit` и `drain`.
    original_created = record.created
    record.created = created
    try:
        asctime = logging.Formatter().formatTime(record, datefmt=_LOG_DATEFMT)
    finally:
        record.created = original_created

    return f"{asctime} [{record.levelname}] {record.name}: {rendered}\n"


def _drain_log_queue(log_queue: queue.Queue) -> str:
    """Слить все записи из очереди в строку через `_format_record`.

    Использует `queue.get_nowait`, чтобы не блокировать вызывающий
    поток: после выполнения примера в очереди лежат все записи,
    собранные `_SnapshottingQueueHandler`'ом, и мы забираем их
    без ожидания.
    """
    chunks: list[str] = []
    while True:
        try:
            record = log_queue.get_nowait()
        except queue.Empty:
            break
        chunks.append(_format_record(record))
    return "".join(chunks)


def run_example(name: str) -> str:
    """Запустить пример `name` и вернуть объединённый захваченный вывод.

    Алгоритм:
    1. Разрешить дескриптор по id (KeyError с подсказкой при ошибке).
    2. В `try`:
       - Подменить `sys.stdout` и `sys.stderr` на `io.StringIO`.
       - Подключить `_SnapshottingQueueHandler` к корневому логгеру
         с уровнем `INFO`; записи складываются в `queue.Queue`.
    3. Вызвать `descriptor.runner()`.
    4. В `finally` — восстановить `sys.stdout`/`sys.stderr` и снять
       handler с логгера. Исключения из примера не подавляются и
       пробрасываются дальше, но ресурсы всё равно корректно
       восстанавливаются.

    Возвращаемое значение — конкатенация stdout, stderr и строк лога
    в том порядке, в каком они были собраны. Точный порядок между
    каналами не гарантирован (всё собирается в разных буферах), но
    внутри каждого канала порядок сохраняется.
    """
    descriptor = get_example(name)

    # Буферы для захвата stdout/stderr. Создаём заранее, чтобы можно
    # было прочитать их в `finally` даже при исключении в примере.
    stdout_buffer = io.StringIO()
    stderr_buffer = io.StringIO()

    log_queue: queue.Queue = queue.Queue()
    queue_handler = _SnapshottingQueueHandler(log_queue)
    queue_handler.setLevel(logging.INFO)

    root_logger = logging.getLogger()
    previous_level = root_logger.level
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(queue_handler)

    try:
        with (
            contextlib.redirect_stdout(stdout_buffer),
            contextlib.redirect_stderr(stderr_buffer),
        ):
            descriptor.runner()
    finally:
        # Восстановление логгера ДО чтения буферов: некоторые примеры
        # логируют при выходе из блоков, и handler должен быть на месте,
        # пока мы сливаем очередь. После drain — снимаем handler и
        # возвращаем прежний уровень корневого логгера.
        log_text = _drain_log_queue(log_queue)
        root_logger.removeHandler(queue_handler)
        root_logger.setLevel(previous_level)

    stdout_text = stdout_buffer.getvalue()
    stderr_text = stderr_buffer.getvalue()

    return stdout_text + stderr_text + log_text
