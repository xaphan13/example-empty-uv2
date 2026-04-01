import logging
import logging.handlers

import os
from logging.handlers import QueueHandler
from multiprocessing import Queue


LOG_DIR = "./log"
LOG_FILE = "empty-uv2.log"


# Создаем глобальный логгер
name_logger = "multi_logger"
multi_logger = logging.getLogger(name_logger)
multi_logger.setLevel(logging.INFO)


class SingletonQueueLogger:
    def __init__(self, log_dir, log_file):
        self.log_multi_queue = None
        self.log_dir = log_dir
        self.log_file = log_file
        self.path_log_file = f"{self.log_dir}\\{self.log_file}"

    def create_queue(self):
        if self.log_multi_queue is None:
            self.log_multi_queue = Queue()

    def create_log_dir(self):
        if not os.path.exists(self.path_log_file):
            os.mkdir(self.path_log_file)

    def get_path_log(self):
        return self.path_log_file

    def get_queue(self):
        return self.log_multi_queue


logger_settings = SingletonQueueLogger(LOG_DIR, LOG_FILE)


def main_process_start_logging():
    logger_settings.create_log_dir()
    logger_settings.create_queue()

    handler = logging.FileHandler(logger_settings.get_path_log())

    listener = logging.handlers.QueueListener(logger_settings.get_queue(), handler)
    listener.start()
    return logger_settings.get_queue(), listener


formProc1 = (
    "/* %(asctime)s - %(module)s.%(funcName)s(%(lineno)d) - "
    "[%(processName)s] - [%(process)d] */"
    "\n%(levelname)s: %(message)s"
)

formProc2 = (
    "/* %(asctime)s - %(module)s.%(funcName)s(%(lineno)d) - "
    "[%(processName)s]  - [%(threadName)s] */"
    "\n%(levelname)s: %(message)s"
)


def every_process_create_queue_handler(log_queue):
    formatter = logging.Formatter(formProc2)

    handler: QueueHandler = logging.handlers.QueueHandler(log_queue)
    handler.setLevel(logging.INFO)
    handler.setFormatter(formatter)

    multi_logger.addHandler(handler)
