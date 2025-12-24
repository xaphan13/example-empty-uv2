from config_log import ConfigLogger

logF = ConfigLogger.get_logger("OnlyFile")

import time

from streamz import Stream


def run_streamz_example():
    source = Stream()

    pipeline = source.map(lambda x1: x1 * 2)
    pipeline.sink(print)  # подписка нужна, иначе элементы пропадут

    results = source.map(lambda x2: x2**2).sink_to_list()

    squares = source.map(lambda x3: x3**2).filter(lambda x4: x4 % 2 == 0).map(lambda x5: x5 + 1).sink_to_list()

    numbers = [1, 2, 3, 4, 5]
    for x in numbers:
        f = source.emit(x)
        # print(type(f))

    print(results)
    print(squares)


def run_streamz_example_1():
    numbers = [1, 2, 3, 4, 5]
    # Создаем источник из итерируемого объекта
    source = Stream.from_iterable(numbers)

    # Строим пайплайн с sink для сохранения результатов
    results = []
    source.map(lambda x: x**2).sink(results.append)

    squares = source.map(lambda x3: x3**2).filter(lambda x4: x4 % 2 == 0).map(lambda x5: x5 + 1).sink_to_list()

    # Запускаем поток
    source.start()
    time.sleep(0.001)

    # Теперь можем увидеть результаты
    print(results)
    print(squares)


def run_streamz_example_2():
    numbers = [10, 20, 30, 40, 50]
    # Создаем источник из итерируемого объекта
    source = Stream.from_iterable(numbers)

    # Строим пайплайн и собираем в список
    results = source.map(lambda x: x**2).sink_to_list()

    # Запускаем поток
    source.start()
    time.sleep(0.001)

    # Теперь можем увидеть результаты
    print(results)  # Выведет [1, 4, 9, 16, 25]
