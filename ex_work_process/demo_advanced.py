import logging
import time

from ex_work_process.advanced_pool import CustomProcessPool

# Настраиваем базовое логирование только для консоли.
# Это позволит избежать проблем с глобальным логгером, использующим пути Windows.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(processName)s] - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


def run_advanced_demo():
    """
    Демонстрационная функция для показа возможностей кастомного пула процессов.
    В этой функции мы:
    1. Инициализируем пул из 3 воркеров.
    2. Создаем набор задач по поиску простых чисел в разных диапазонах.
    3. Отправляем задачи в пул и дожидаемся их выполнения (map_tasks).
    4. Выводим статистику и результаты.
    5. Корректно завершаем пул.
    """
    logger.info("=== Запуск демонстрации продвинутой работы с процессами (Advanced Pool) ===")

    # Определяем количество воркеров. Оптимально - по числу ядер процессора.
    NUM_WORKERS = 3
    pool = CustomProcessPool(num_workers=NUM_WORKERS)

    # Запускаем пул. Процессы будут созданы и начнут ждать задачи в очереди.
    pool.start()

    # Подготавливаем практические задачи (поиск простых чисел в диапазонах).
    # Используем достаточно большие диапазоны, чтобы вычисления заняли заметное время.
    tasks = [
        {"task_id": "Task-A", "start": 100_000, "end": 120_000},
        {"task_id": "Task-B", "start": 200_000, "end": 220_000},
        {"task_id": "Task-C", "start": 300_000, "end": 320_000},
        {"task_id": "Task-D", "start": 400_000, "end": 420_000},
        {"task_id": "Task-E", "start": 500_000, "end": 520_000},
    ]

    logger.info("Начинаем распределение задач по пулу...")

    # Засекаем общее время на обработку всех задач
    t0 = time.time()

    # Метод map_tasks раздаст задачи и заблокирует выполнение до получения всех ответов
    results = pool.map_tasks(tasks)

    total_time = time.time() - t0

    logger.info(f"=== Все {len(tasks)} задач обработаны за {total_time:.4f} сек. ===")
    logger.info("Результаты выполнения:")

    # Сортируем результаты по task_id для красивого вывода
    results.sort(key=lambda x: x.get("task_id", ""))

    for res in results:
        task_id = res.get('task_id')
        worker = res.get('worker_name')
        count = res.get('primes_count')
        el_time = res.get('elapsed_time')
        sample = res.get('sample_primes')

        logger.info(f"  [{task_id}] Выполнена {worker} за {el_time}s. "
                    f"Найдено простых чисел: {count}. Примеры: {sample}")

    # Корректно завершаем все процессы (отправка STOP_SIGNAL)
    pool.stop()
    logger.info("=== Демонстрация успешно завершена ===")


if __name__ == "__main__":
    run_advanced_demo()
