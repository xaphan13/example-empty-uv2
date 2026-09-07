import time
import os
import math
from concurrent.futures import ProcessPoolExecutor, as_completed
from multiprocessing import cpu_count

from config_multi_proc_log import (
    multi_logger as logF,
    main_process_start_logging,
    every_process_create_queue_handler,
    logger_settings,
)

from ex_work_process.practical_task import factorize

def init_worker(log_queue):
    """
    Функция инициализации (initializer), которая вызывается единожды для каждого дочернего процесса
    при его создании внутри пула. Настраивает обработчик логирования для дочернего процесса.

    Args:
        log_queue (multiprocessing.Queue): Общая очередь, в которую будут складываться логи от всех процессов
                                          перед их записью в файл главным процессом (или специальным потоком).
    """
    # Добавляем обработчик, который перехватывает записи журнала
    # в дочернем процессе и отправляет их в общую очередь главного процесса.
    every_process_create_queue_handler(log_queue)
    logF.info(f"Рабочий процесс инициализирован (PID: {os.getpid()})")


def run_pool_demo():
    """
    Демонстрационная функция, запускающая пул процессов (ProcessPoolExecutor) для параллельного
    выполнения ресурсоемкой задачи факторизации.
    Функция демонстрирует правильную работу с многопроцессным логированием через очередь.
    """
    logF.info("Запуск демо: ProcessPoolExecutor с задачей факторизации (CPU-bound)")

    # Создаем директорию для логов, если ее нет, чтобы избежать ошибки IsADirectoryError
    # или FileNotFoundError
    log_dir_path = logger_settings.log_dir
    if not os.path.exists(log_dir_path):
        os.makedirs(log_dir_path)

    path_log_file = logger_settings.get_path_log()

    try:
        if os.path.isdir(path_log_file):
            os.rmdir(path_log_file)
    except Exception:
        pass

    # Настраиваем централизованное логирование: запускаем QueueListener,
    # который будет записывать все логи в файл (в нашем случае 'empty-uv2.log').
    try:
        log_queue, listener = main_process_start_logging()
    except IsADirectoryError:
        logF.error("Ошибка логирования. Файл лога распознан как директория. Попытка исправить.")
        os.rmdir(path_log_file)
        log_queue, listener = main_process_start_logging()

    # Подготовим список чисел, факторизацию которых будем производить параллельно.
    # Большие числа выбраны для того, чтобы наглядно загрузить процессор
    # и продемонстрировать эффект распараллеливания.
    # Пример больших чисел (намеренно усложняем вычисления для демо):
    numbers_to_factorize = [
        123456789,
        987654321,
        293847563,
        485736251,
        100000000,
        500000000,
        2147483647, # Большое простое число Мерсенна для долгой обработки
        777777777,
        111111111,
        999999999
    ]

    # Определяем оптимальное количество рабочих процессов: обычно равно числу ядер процессора.
    # Это позволяет избежать излишнего переключения контекста и накладных расходов.
    max_workers = cpu_count()
    logF.info(f"Используем {max_workers} процессов для выполнения задач.")

    start_time = time.time()

    # ProcessPoolExecutor позволяет удобно распределять задачи между процессами.
    # Параметр initializer позволяет выполнить настройку каждого нового дочернего процесса,
    # а initargs передает аргументы в функцию initializer.
    with ProcessPoolExecutor(max_workers=max_workers, initializer=init_worker, initargs=(log_queue,)) as executor:

        # Размещаем задачи (submit) в пул процессов.
        # Метод submit возвращает объект Future, представляющий собой отложенный результат.
        future_to_number = {
            executor.submit(factorize, number): number
            for number in numbers_to_factorize
        }

        logF.info("Все задачи отправлены в пул процессов. Ожидание завершения...")

        # Получаем результаты по мере их завершения с помощью функции as_completed.
        # Это эффективный способ собирать результаты без строгой очередности.
        for future in as_completed(future_to_number):
            number = future_to_number[future]
            try:
                # Получаем результат факторизации
                result_factors = future.result()
                # Выводим количество найденных делителей
                logF.info(f"В главном процессе: Число {number} успешно обработано. Найдено делителей: {len(result_factors)}.")
            except Exception as exc:
                # В случае ошибки при выполнении задачи в дочернем процессе перехватываем и логируем её.
                logF.error(f"Задача для числа {number} завершилась с ошибкой: {exc}")

    end_time = time.time()
    total_time = end_time - start_time

    logF.info(f"Демо завершено. Общее время выполнения всех задач составило: {total_time:.4f} секунд.")

    # Останавливаем слушателя логов, чтобы корректно завершить запись и очистить ресурсы.
    listener.stop()

if __name__ == "__main__":
    run_pool_demo()