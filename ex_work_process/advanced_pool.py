import logging
from multiprocessing import Queue
from ex_work_process.advanced_worker import MathWorkerProcess
from queue import Empty

# Логгер для пула процессов
logger = logging.getLogger(__name__)

class CustomProcessPool:
    """
    Кастомный менеджер пула процессов.
    Пул процессов позволяет управлять группой рабочих процессов (воркеров),
    передавать им задачи и собирать результаты.
    Использование пула процессов является хорошей практикой в Python, так как
    позволяет избежать накладных расходов на постоянное создание и уничтожение
    процессов для каждой отдельной задачи.
    """

    def __init__(self, num_workers):
        """
        Инициализация пула процессов.

        Args:
            num_workers (int): Количество воркеров, которые будут созданы в пуле.
        """
        self.num_workers = num_workers
        self.workers = []

        # Очереди для связи с воркерами.
        # in_queue используется для раздачи задач воркерам.
        # out_queue используется для сбора результатов от воркеров.
        self.in_queue = Queue()
        self.out_queue = Queue()

    def start(self):
        """
        Запуск всех процессов в пуле.
        Процессы создаются и сразу начинают ожидать задачи из in_queue.
        """
        logger.info(f"Запуск пула процессов из {self.num_workers} воркеров...")
        for i in range(self.num_workers):
            worker_name = f"Worker-{i+1}"
            # Создаем экземпляр нашего продвинутого воркера
            worker = MathWorkerProcess(in_queue=self.in_queue, out_queue=self.out_queue, name=worker_name)
            self.workers.append(worker)
            worker.start()
        logger.info("Все воркеры пула запущены.")

    def map_tasks(self, tasks):
        """
        Распределяет список задач по воркерам и собирает результаты.
        Этот метод блокирующий — он возвращает управление только после того,
        как все задачи будут обработаны.

        Args:
            tasks (list): Список словарей с параметрами задач.
                Например: [{"task_id": 1, "start": 1, "end": 1000}, ...]

        Returns:
            list: Список результатов от воркеров.
        """
        num_tasks = len(tasks)
        if num_tasks == 0:
            return []

        logger.info(f"Добавление {num_tasks} задач в очередь...")

        # 1. Помещаем все задачи во входную очередь.
        # Воркеры, которые уже запущены, автоматически начнут брать их оттуда.
        for task in tasks:
            self.in_queue.put(task)

        results = []
        tasks_completed = 0

        # 2. Ожидаем и собираем результаты.
        # Цикл работает до тех пор, пока количество полученных результатов
        # не станет равным количеству отправленных задач.
        logger.info("Ожидание выполнения задач...")
        while tasks_completed < num_tasks:
            try:
                # Пытаемся получить результат с таймаутом, чтобы не зависнуть навечно
                result = self.out_queue.get(timeout=2)
                results.append(result)
                tasks_completed += 1
                logger.debug(f"Получен результат {tasks_completed}/{num_tasks}")
            except Empty:
                # Если за 2 секунды результатов не поступило, мы просто ждем дальше
                # Можно было бы здесь добавить проверки на то, живы ли воркеры (worker.is_alive()),
                # чтобы корректно обработать ситуацию падения воркера
                alive_workers = any(w.is_alive() for w in self.workers)
                if not alive_workers:
                    logger.error("Все воркеры завершились или упали до завершения задач!")
                    break

        logger.info("Все задачи успешно завершены.")
        return results

    def stop(self):
        """
        Корректная остановка пула процессов.
        Отправляет каждому воркеру специальный сигнал на остановку (STOP_SIGNAL)
        и дожидается завершения (join) каждого процесса.
        """
        logger.info("Остановка пула процессов...")

        # Отправляем сигнал остановки каждому воркеру
        for _ in self.workers:
            self.in_queue.put(MathWorkerProcess.STOP_SIGNAL)

        # Ждем, пока каждый воркер не завершит свою работу
        for worker in self.workers:
            worker.join()

        logger.info("Все процессы пула корректно остановлены.")
