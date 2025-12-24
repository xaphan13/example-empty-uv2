from config_log import ConfigLogger

logF = ConfigLogger.get_logger("OnlyFile")
from dis import dis


def func_list_add(x, list_ex=[]):
    for i in range(x):
        list_ex.append(i * i)
    return list_ex


def run_f():
    # print(func_list_add(2), func_list_add(3, [3, 2, 1]), func_list_add(3))
    logF.info("%s, %s, %s", func_list_add(2), func_list_add(3, [3, 2, 1]), func_list_add(3))
    # logF.info(f"{func_list_add(2)}, {func_list_add(3, [3, 2, 1])}, {func_list_add(3)}")


def trap_1():
    logF.info(f"'****' trap_1 - 'start'")

    # dis(run_f)
    run_f()
