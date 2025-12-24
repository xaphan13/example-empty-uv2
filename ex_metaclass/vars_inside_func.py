from config_log import ConfigLogger
from debug_info import dbg_info_closure, dbg_info_frame

logF = ConfigLogger.get_logger("OnlyFile")
logC = ConfigLogger.get_logger("Stdout")

import dis
import inspect


funcs1 = []
funcs2 = []


# случай 1: модульный уровень — i глобальная (модульная)
for i in range(3):

    def func_global(y=55):
        global i
        i = 99
        dbg_info_frame(inspect.currentframe(), "func_global")
        return i, y

    funcs1.append(func_global)


# случай 2: внутри функции — i локальная для outer, а для inner — свободная (замкнутая)
def outer(a=77):
    for n in range(3):

        def inner(x=44):
            nonlocal n
            dbg_info_frame(inspect.currentframe(), "inner")
            n = 10
            return n, x

        funcs2.append(inner)

    n = 5
    dbg_info_frame(inspect.currentframe(), "outer")
    return a, n


def run_demo():
    # Логирование всех глобальных переменных модуля (без служебных и logF)
    module_globals = {k: v for k, v in globals().items() if not k.startswith("__") and k != "logF"}  # noqa: F841
    # logF.info(f"Глобальные переменные модуля: {module_globals}")

    outer()

    logC.info(f"--------------dis.dis(outer)")
    dis.dis(outer)
    logC.info(f"--------------dis.dis(funcs1[0])")
    dis.dis(funcs1[0])
    logC.info(f"--------------dis.dis(funcs2[0])")
    dis.dis(funcs2[0])

    dbg_info_closure(outer)
    dbg_info_closure(funcs2[0])
    funcs2[0](7)
    funcs2[1](9)

    dbg_info_closure(funcs1[0])
    funcs1[0](7)
