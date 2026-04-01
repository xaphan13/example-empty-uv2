from config_multi_proc_log import (
    multi_logger,
    every_process_create_queue_handler,
)

logF = multi_logger

import os
from multiprocessing import Process, current_process
from queue import Empty


class Process_work(Process):
    """
    Класс для выполнения работы в отдельном процессе.
    Обрабатывает данные из входной очереди и отправляет результаты в выходную очередь.
    """

    STOP_SIGNAL = {"type": "stop"}
    READ_TIMEOUT_SEC = 1

    def __init__(self, log_queue, in_queue, out_queue, name=None):
        """
        log_queue: Очередь для логирования
        in_queue: Входная очередь данных
        out_queue: Выходная очередь результатов
        name: Имя процесса
        """
        self.proc = None
        self.log_queue = log_queue
        self.out_queue = out_queue
        self.in_queue = in_queue
        super().__init__(name=name)

    def _read_from_input_queue(self):
        """
        Чтение данных из входной очереди с тайм-аутом

        Returns:
            Данные из очереди или None если тайм-аут
        """
        try:
            return self.in_queue.get(timeout=self.READ_TIMEOUT_SEC)
        except Empty:
            logF.info("Process_work no data, continuing...")
            return None
        except Exception as e:
            logF.error(f"Error reading from input queue: {e}")
            return None

    def print_info_process(self):
        self.proc = current_process()
        logF.info(f"Process_work RUN -> name={self.proc.name}, pid={self.proc.pid}, parent_pid={os.getppid()}")

    def run(self):
        every_process_create_queue_handler(self.log_queue)
        self.print_info_process()

        try:
            while True:
                indata = self._read_from_input_queue()

                if indata is None:
                    continue

                if indata == self.STOP_SIGNAL:
                    logF.info(f"Process_work {self.proc.name} received STOP_SIGNAL")
                    break

                # Обработка данных и отправка результата
                result = {"worker": self.proc.name, "data": indata}

                try:
                    self.out_queue.put(result)
                    logF.info(f"Process_work {self.proc.name} processed {indata=}")
                except Exception as e:
                    logF.error(f"Error putting result to output queue: {e}")

        except KeyboardInterrupt:
            logF.info(f"Process_work {self.proc.name} interrupted by keyboard")
        except Exception as e:
            logF.error(f"Unexpected error in Process_work {self.proc.name}: {e}")
        finally:
            logF.info(f"Process_work {self.proc.name} finished")
