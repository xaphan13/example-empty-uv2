import inspect
import pathlib
import sys

from config_log import ConfigLogger

logF = ConfigLogger.get_logger("OnlyFile")

import ex_all_others.my_module as my_module
from dis import dis
from debug_info import dbg_info_func, dbg_info_closure


def process_arbitrary_params(*args):
    print("Позиционные аргументы:", args)


# Примеры использования
def process():
    names = ["Alice", "Bob", "Charlie"]
    process_arbitrary_params(*names)
    process_arbitrary_params("Alice", "Bob", "Charlie")


def dis_mod():
    logF.info(f"'****' dis_mod - 'start'")

    dir_current = pathlib.Path(__file__).parent
    path = pathlib.Path(dir_current, "my_module.py")  # noqa: F841

    m = sys.modules.get("ex_all_others.my_module")  # модуль уже импортирован

    src, filename = inspect.getsource(m), getattr(m, "__file__", "<string>")
    code = compile(src, filename, "exec")
    # src = path.read_text(encoding='utf-8')
    # code = compile(src, str(path), 'exec')

    print(src)
    dis(code)

    dis(process)
    process()
