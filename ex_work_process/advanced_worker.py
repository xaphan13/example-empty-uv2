import os
import time
import math
import logging
from multiprocessing import Process, current_process
from queue import Empty

# Логгер для записи информации о работе процесса
logger = logging.getLogger(__name__)

class MathWorkerProcess(Process):
    """
    Класс для выполнения вычислительно сложных задач в отдельном процессе.
    Наследуется от multiprocessing.Process.
    В данном примере класс используется для нахождения всех простых чисел в заданном диапазоне
    или разложения числа на множители.
    """

    # Сигнал для корректного завершения работы процесса
    STOP_SIGNAL = {"type": "stop"}

    # Таймаут при ожидании новой задачи из очереди.
    # Позволяет не блокировать процесс навечно и периодически проверять другие условия.
    READ_TIMEOUT_SEC = 1

    def __init__(self, in_queue, out_queue, name=None):
        """
        Инициализация процесса воркера.

        Args:
            in_queue (multiprocessing.Queue): Очередь для получения задач.
            out_queue (multiprocessing.Queue): Очередь для отправки результатов.
            name (str, optional): Имя процесса (будет видно в логах или системном мониторе).
        """
        super().__init__(name=name)
        self.in_queue = in_queue
        self.out_queue = out_queue
        self.proc = None  # Ссылка на текущий процесс (установится в методе run)

    def _read_from_input_queue(self):
        """
        Внутренний метод для безопасного чтения задачи из входной очереди.
        Использует таймаут для предотвращения вечной блокировки.

        Returns:
            Словарь с задачей, STOP_SIGNAL или None (если очередь пуста по таймауту).
        """
        try:
            return self.in_queue.get(timeout=self.READ_TIMEOUT_SEC)
        except Empty:
            # Если очередь пуста, просто возвращаем None и продолжаем цикл
            return None
        except Exception as e:
            logger.error(f"[{self.name}] Ошибка при чтении из очереди: {e}")
            return None

    def calculate_primes(self, start, end):
        """
        Практическая задача: поиск всех простых чисел в диапазоне от start до end.

        Args:
            start (int): Начало диапазона.
            end (int): Конец диапазона.

        Returns:
            list: Список простых чисел в заданном диапазоне.
        """
        primes = []
        for n in range(max(2, start), end + 1):
            is_prime = True
            # Проверяем делимость числа до его квадратного корня (оптимизация)
            for i in range(2, int(math.sqrt(n)) + 1):
                if n % i == 0:
                    is_prime = False
                    break
            if is_prime:
                primes.append(n)
        return primes

    def run(self):
        """
        Главный метод процесса, который вызывается при старте.
        Содержит бесконечный цикл обработки задач, пока не будет получен STOP_SIGNAL.
        """
        self.proc = current_process()
        logger.info(f"Воркер ЗАПУЩЕН -> имя={self.proc.name}, pid={self.proc.pid}, родительский_pid={os.getppid()}")

        try:
            while True:
                # Получаем новую задачу из очереди
                task = self._read_from_input_queue()

                # Если по таймауту ничего не пришло, пробуем снова
                if task is None:
                    continue

                # Проверяем, не является ли задача сигналом к остановке
                if task == self.STOP_SIGNAL:
                    logger.info(f"[{self.proc.name}] Получен сигнал STOP_SIGNAL. Завершаю работу.")
                    break

                # Извлекаем данные для выполнения задачи
                task_id = task.get("task_id")
                start_range = task.get("start", 0)
                end_range = task.get("end", 0)

                logger.info(f"[{self.proc.name}] Взял задачу {task_id}: поиск простых чисел в диапазоне [{start_range}, {end_range}]")

                # Имитируем тяжелую работу (может быть убрано в реальном коде)
                start_time = time.time()

                # Выполняем саму вычислительную задачу
                result_data = self.calculate_primes(start_range, end_range)

                elapsed_time = time.time() - start_time

                # Формируем результат для отправки обратно
                result = {
                    "task_id": task_id,
                    "worker_name": self.proc.name,
                    "worker_pid": self.proc.pid,
                    "primes_count": len(result_data),
                    "elapsed_time": round(elapsed_time, 4),
                    # В реальных приложениях пересылать большие массивы данных через очереди
                    # может быть накладно, но для примера мы отправляем часть данных
                    "sample_primes": result_data[:5] if result_data else []
                }

                try:
                    # Отправляем результат в выходную очередь
                    self.out_queue.put(result)
                    logger.info(f"[{self.proc.name}] Задача {task_id} выполнена за {elapsed_time:.4f} сек.")
                except Exception as e:
                    logger.error(f"[{self.proc.name}] Ошибка при отправке результата в выходную очередь: {e}")

        except KeyboardInterrupt:
            logger.warning(f"[{self.proc.name}] Прервано пользователем (KeyboardInterrupt)")
        except Exception as e:
            logger.error(f"[{self.proc.name}] Неожиданная ошибка во время работы воркера: {e}")
        finally:
            logger.info(f"Воркер {self.proc.name} (pid={self.proc.pid}) ЗАВЕРШИЛ работу.")
