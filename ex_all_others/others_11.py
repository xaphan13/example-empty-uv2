from config_log import ConfigLogger

logF = ConfigLogger.get_logger("OnlyFile")


def others_11_start():
    logF.info(f"'****' others_11_start - 'start'")

    logF.info("Hello, {name}!".format(name="John"))

    t = "Hello, {name}!"
    logF.info(t.format(name="John"))

    s = "Hello, %(name)s!"
    logF.info(s % {"name": "John"})

    logF.info({1, 2, 3} | {3, 4} == {1, 2, 3, 4})

    x = {"a": 1, "b": 2}
    y = {"b": 3, "c": 4}
    x |= y  # Эквивалентно x.update(y)
    x.update(y)  # Даёт тот же результат, что и x |= y
    logF.info(x)  # Выведет: {'a': 1, 'b': 3, 'c': 4}

    b = True
    bb = bool(999)
    b.__bool__()

    logF.info(f"{type(bb)}, {id(bb)}, {id(b)}, {True.__bool__()}")
