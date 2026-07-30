"""
Пример улучшенного использования многопроцессности (Multiprocessing) в Python.

Вместо ручного управления классами Process и очередями (Queue), здесь используется
современный подход с помощью concurrent.futures.ProcessPoolExecutor.

Улучшения по сравнению с базовым подходом:
1. Автоматическое управление пулом воркеров (не нужно вручную создавать и завершать процессы).
2. Обработка ошибок внутри процессов прозрачно передается в главный процесс.
3. Меньше boilerplate-кода для очередей (in_queue, out_queue).
4. Задачи (tasks) имеют более практический, процессорозависимый (CPU-bound) характер:
   поиск простых чисел в заданном диапазоне, что является классическим примером
   задачи, которая выигрывает от использования multiprocessing в Python из-за GIL.
"""

import concurrent.futures
import time
import os
from dataclasses import dataclass
from typing import List

# Data classes
@dataclass
class TaskInput:
    """Описывает входные данные для задачи."""
    task_id: int
    start_num: int
    end_num: int

@dataclass
class TaskResult:
    """Описывает результат выполнения задачи."""
    task_id: int
    worker_pid: int
    primes_count: int
    execution_time: float


def is_prime(n: int) -> bool:
    """
    Проверяет, является ли число простым.

    Args:
        n: Целое число для проверки.

    Returns:
        True, если число простое, иначе False.
    """
    if n <= 1:
        return False
    if n <= 3:
        return True
    if n % 2 == 0 or n % 3 == 0:
        return False
    i = 5
    while i * i <= n:
        if n % i == 0 or n % (i + 2) == 0:
            return False
        i += 6
    return True


def count_primes_in_range(task_input: TaskInput) -> TaskResult:
    """
    Практическая задача: подсчет количества простых чисел в заданном диапазоне.
    Выполняется в отдельном процессе из пула.

    Args:
        task_input (TaskInput): Входные данные задачи.

    Returns:
        TaskResult: Результат выполнения с метриками.
    """
    start_time = time.time()

    # Получаем ID текущего процесса, чтобы показать, что задачи выполняются параллельно
    current_pid = os.getpid()
    print(f"[Worker PID: {current_pid}] Начало выполнения задачи {task_input.task_id} "
          f"(диапазон: {task_input.start_num} - {task_input.end_num})")

    primes_count = 0
    for num in range(task_input.start_num, task_input.end_num + 1):
        if is_prime(num):
            primes_count += 1

    execution_time = time.time() - start_time
    print(f"[Worker PID: {current_pid}] Задача {task_input.task_id} завершена "
          f"за {execution_time:.4f} сек. Найдено простых чисел: {primes_count}")

    return TaskResult(
        task_id=task_input.task_id,
        worker_pid=current_pid,
        primes_count=primes_count,
        execution_time=execution_time
    )


def run_improved_pool_demo():
    """
    Главная функция для демонстрации работы с ProcessPoolExecutor.
    Создает набор задач, отправляет их в пул процессов и собирает результаты.
    """
    print(f"[Main PID: {os.getpid()}] Запуск улучшенного примера многопроцессности...")

    # Формируем список задач (практическая, тяжелая для CPU работа)
    ranges = [
        (1, 1_000_000),
        (1_000_001, 2_000_000),
        (2_000_001, 3_000_000),
        (3_000_001, 4_000_000),
        (4_000_001, 5_000_000),
        (5_000_001, 6_000_000),
    ]

    tasks = [
        TaskInput(task_id=i, start_num=r[0], end_num=r[1])
        for i, r in enumerate(ranges, 1)
    ]

    start_total_time = time.time()

    # Используем ProcessPoolExecutor
    # max_workers по умолчанию равен количеству логических ядер процессора
    results: List[TaskResult] = []

    # Менеджер контекста 'with' гарантирует корректное освобождение ресурсов
    # пула процессов (вызов pool.shutdown() под капотом).
    with concurrent.futures.ProcessPoolExecutor() as executor:
        # map() автоматически распределяет задачи (tasks) по процессам из пула
        # и возвращает результаты в том же порядке, в котором были переданы задачи.
        # Для более сложного контроля можно использовать executor.submit() и as_completed().
        for result in executor.map(count_primes_in_range, tasks):
            results.append(result)

    total_time = time.time() - start_total_time

    # Вывод итоговых результатов
    print("\n--- ИТОГОВЫЕ РЕЗУЛЬТАТЫ ---")
    total_primes = 0
    for res in results:
        print(f"Задача {res.task_id} (PID {res.worker_pid}): {res.primes_count} простых чисел, "
              f"время выполнения: {res.execution_time:.4f} сек")
        total_primes += res.primes_count

    print(f"Общее количество простых чисел: {total_primes}")
    print(f"Общее время выполнения пула: {total_time:.4f} сек")
    print(f"Использование пула процессов позволило распараллелить вычисления "
          f"и существенно сократить общее время.")

if __name__ == '__main__':
    run_improved_pool_demo()
