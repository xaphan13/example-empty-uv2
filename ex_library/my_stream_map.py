from config_log import ConfigLogger

logF = ConfigLogger.get_logger("OnlyFile")

import itertools


def flatMap_func(param):
    return param, param + 1


def chain_maps():
    numbers = [2, 3, 4, 5, 6]

    # Первый map: возводим в квадрат
    map1 = map(lambda x: x**2, numbers)

    # Второй map: из каждого элемента получаем пару (элемент, элемент+1)
    map2 = map(flatMap_func, map1)
    # из кортежей снова поток элементов
    flat_iter = itertools.chain.from_iterable(map2)

    # Третий map:
    filter3 = filter(lambda x: x <= 36, flat_iter)

    # Четвертый map: преобразуем в строку
    map4 = map(str, filter3)

    list4 = list(map4)
    logF.info(f"list4: {list4}")
