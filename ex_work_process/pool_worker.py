import time
import os
import hashlib

from config_multi_proc_log import multi_logger, every_process_create_queue_handler

# Глобальная переменная для каждого рабочего процесса
_log_queue = None

logF = multi_logger

def init_worker(log_queue):
    """
    Инициализатор для каждого процесса в пуле.
    Вызывается один раз при создании рабочего процесса (worker-а).

    Args:
        log_queue: мультипроцессорная очередь для логов, передаваемая из главного процесса.
    """
    global _log_queue
    _log_queue = log_queue
    # Настраиваем логирование для данного процесса
    every_process_create_queue_handler(_log_queue)

    logF.info(f"Worker initialized: PID={os.getpid()}, Parent PID={os.getppid()}")

def perform_heavy_computation(task_data):
    """
    Практическая задача для рабочего процесса: симуляция ресурсоемких вычислений.
    Функция генерирует хеши SHA-256 для поиска определенного префикса (аналог 'майнинга' или Proof-of-Work).

    Args:
        task_data (dict): Словарь с данными задачи, содержащий 'task_id' и 'difficulty' (количество нулей в начале хеша).

    Returns:
        dict: Результат вычислений, содержащий исходные данные, найденное число (nonce), итоговый хеш и затраченное время.
    """
    task_id = task_data.get("task_id", "unknown")
    difficulty = task_data.get("difficulty", 4)
    prefix = "0" * difficulty

    logF.info(f"Worker PID={os.getpid()} started task '{task_id}' with difficulty {difficulty}")

    start_time = time.time()
    nonce = 0
    while True:
        # Формируем строку и вычисляем ее хеш
        text = f"{task_id}-{nonce}".encode('utf-8')
        current_hash = hashlib.sha256(text).hexdigest()

        # Проверяем условие сложности (начинается ли хеш с заданного числа нулей)
        if current_hash.startswith(prefix):
            break
        nonce += 1

    elapsed_time = time.time() - start_time

    logF.info(f"Worker PID={os.getpid()} finished task '{task_id}' in {elapsed_time:.4f}s. Nonce found: {nonce}")

    return {
        "task_id": task_id,
        "nonce": nonce,
        "hash": current_hash,
        "elapsed_time": elapsed_time,
        "worker_pid": os.getpid()
    }
