from config_log import ConfigLogger

logF = ConfigLogger.get_logger("OnlyFile")

from dis import dis
from debug_info import dbg_info_func, dbg_info_closure


# ------------------------------------------------------------------------
glob = 10


def outer(y=1):
    global glob
    glob = glob + 3

    def inner():
        global glob
        nonlocal x
        x, glob = x + 5, glob + 1
        return x, glob

    dbg_info_closure(inner)

    x = 30
    logF.info(f"clo - {x} - {inner.__closure__[0].cell_contents} - {inner.__closure__[0]}")
    return inner


def closure_start():
    dis(outer)
    logF.info(f"'****' closure_start - 'start'")

    inner_obj = outer()
    res = inner_obj()

    logF.info(f"inn() - res = {res}")

    dbg_info_func(outer)
    dbg_info_func(inner_obj)


# ------------------------------------------------------------------------


def func():
    from config_log import ConfigLogger
    import dis

    def first(a):
        x = 1

        def second(y=3, z=4):
            nonlocal x
            x = 2
            return x + y + a

        return second

    return first


def closure_new1():
    logF.info(f"'****' closure_new1 - 'start'")
    dis(func)

    a, b, c = 0, 2, 3

    x = a or b and c * 2 and a + 4
    print(x)
