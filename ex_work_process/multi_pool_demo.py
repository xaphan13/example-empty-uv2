import time
from multiprocessing import Pool, cpu_count

from config_multi_proc_log import multi_logger, logger_settings

# Импортируем инициализатор и саму задачу из нового модуля
from ex_work_process.multi_pool_worker import init_worker, perform_heavy_computation

logF = multi_logger


def run_pool_demo(w=None):
    """
    Демонстрация использования multiprocessing. Pool.
    Pool (Пул процессов) — это более удобный и высокоуровневый способ управления рабочими процессами,
    чем ручное создание объектов Process. Пул автоматически распределяет задачи по доступным процессам
    и собирает результаты.
    """
    if w is not None:  # w=None
        return
    logF.info("**** run_pool_demo - 'start' ****")

    # Определяем количество доступных логических ядер процессора
    # Обычно рекомендуется использовать cpu_count() или чуть меньше, чтобы не перегружать систему.
    num_processes = max(1, cpu_count() - 1)
    logF.info(f"Creating process pool with {num_processes} workers.")

    # Получаем очередь для логирования, которая будет передана всем воркерам
    log_queue = logger_settings.get_queue()

    # Генерируем список задач (например, 10 задач с разной сложностью)
    tasks = [{"task_id": f"Task-{i}", "difficulty": 4 if i % 2 == 0 else 5} for i in range(1, 11)]
    logF.info(f"Generated {len(tasks)} tasks for the pool.")

    start_time = time.time()

    # Создаем пул процессов с использованием контекстного менеджера 'with',
    # который гарантирует корректное закрытие пула после завершения работы.
    # Мы передаем init_worker в качестве инициализатора (initializer) пула,
    # и очередь log_queue в качестве аргумента (initargs) для него.
    # Это позволяет каждому процессу в пуле при старте настроить логирование в общую очередь.
    with Pool(processes=num_processes, initializer=init_worker, initargs=(log_queue,)) as pool:
        # Существует несколько способов распределить задачи.
        # 1. pool.map - блокирует выполнение до получения всех результатов и возвращает список результатов.
        # 2. pool.imap / pool.imap_unordered - возвращает итератор. Удобно для потоковой обработки
        # и меньшего потребления памяти, особенно с большим количеством задач.
        # imap_unordered возвращает результаты по мере их готовности (порядок не гарантирован),
        # что часто является самым быстрым способом получения первых результатов.

        logF.info("Starting task processing using pool.imap_unordered...")

        # Используем imap_unordered для асинхронного получения результатов по мере готовности
        results_iterator = pool.imap_unordered(perform_heavy_computation, tasks)

        successful_tasks = 0
        total_time_spent = 0.0

        # Итерируемся по результатам по мере того как воркеры их завершают
        for result in results_iterator:
            successful_tasks += 1
            total_time_spent += result["elapsed_time"]
            logF.info(
                f"Main process received result for {result['task_id']}: "
                f"Hash={result['hash'][:10]}... Nonce={result['nonce']} "
                f"(Worker PID: {result['worker_pid']})"
            )

    total_elapsed = time.time() - start_time

    logF.info("**** run_pool_demo - 'finished' ****")
    logF.info(f"Total tasks completed: {successful_tasks}")
    logF.info(f"Total time spent in workers: {total_time_spent:.2f}s")
    logF.info(f"Wall-clock time: {total_elapsed:.2f}s")
    logF.info(f"Speedup ratio: {(total_time_spent / total_elapsed) if total_elapsed > 0 else 0:.2f}x")
