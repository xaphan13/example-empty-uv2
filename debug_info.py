from config_log import ConfigLogger

logF = ConfigLogger.get_logger("OnlyFile")

from typing import Callable
from types import FrameType
import sys

list_not = [
    "__name__",
    "__doc__",
    "__package__",
    "__loader__",
    "__spec__",
    "__file__",
    "__cached__",
    "__builtins__",
    "__annotations__",
    "Callable",
    "Generator",
    "inspect",
    "sys",
    "ConfigLogger",
    "logFC",
    "logF",
    "inf",
]


def dbg_info_dict(obj):
    mod_dict = obj.__dict__
    s = "\n".join([f"{k} = {v}" for k, v in mod_dict.items()])
    logF.info(
        f"###class : '{obj.__class__}' : ID = {hex(id(obj))}"
        f"\nid.super.class = {hex(id(obj.__class__))} : type.super.class = {type(obj.__class__)}"
        f"\n{s}"
    )


# ------------------------------------------------------------- Module
def dbg_info_module(mod):
    mod_dict = mod.__dict__
    s = "\n".join([f"{k} = {v}" for k, v in mod_dict.items() if k not in list_not])
    logF.info(f"###module : '{mod.__name__}' = {hex(id(mod))} : .__dict__ = {hex(id(mod_dict))}\n{s}")


def dbg_info_name_module(name_mod):
    mod = sys.modules[name_mod]

    mod_dict = mod.__dict__
    s = "\n".join([f"{k} = {v}" for k, v in mod_dict.items() if k not in list_not])
    logF.info(f"###module : '{mod.__name__}' = {hex(id(mod))} : .__dict__ = {hex(id(mod_dict))}\n{s}")


def dbg_info_module_id(mod, var_name="module"):
    logF.info(f"'{var_name}' = {mod.__name__} : id = {hex(id(mod))}")


# ------------------------------------------------------------- Function
def dbg_info_closure(func):
    __name, __module = func.__name__, func.__module__
    logF.info(f"'debug' function : {__name=} = {__module=}")

    if func.__defaults__:
        logF.info(f"FUNC.__defaults__: {func.__defaults__}")

    if hasattr(func, "__closure__") and func.__code__.co_freevars:
        logF.info(f"FUNC.co_freevars: {func.__code__.co_freevars}")
        logF.info(f"FUNC.__closure__ = {func.__closure__}")

    logF.info(f"FUNC.co_varnames: {func.__code__.co_varnames}")
    logF.info(f"FUNC.co_cellvars: {func.__code__.co_cellvars}")


def dbg_info_func(func: Callable):
    __name, __module = func.__name__, func.__module__
    # logFC.info(f"function : '{__name}' = {func.__dict__=}")

    def_s = f"\n.defaults = {func.__defaults__}" if func.__defaults__ is not None else f""
    const_s = f"\n.co_consts = {func.__code__.co_consts}"

    if hasattr(func, "__closure__") and func.__code__.co_freevars:
        logF.info(
            f"###funct### : '{__name}' - {hex(id(func))} - mod[{__module}]"
            # f"\n.__globals__ = {hex(id(func.__globals__))}"
            f"{def_s}"
            f"{const_s}"
            f"\n.co_freevars = {func.__code__.co_freevars}"
            f"\n.__closure__ = {tuple(closure.cell_contents for closure in func.__closure__)}"
            f"\n.__closure__ = {func.__closure__}"
        )
    else:
        logF.info(
            f"###funct### : '{__name}' - {hex(id(func))} - mod[{__module}]"
            # f"\n.__globals__ = {hex(id(func.__globals__))}"
            f"{def_s}"
            f"{const_s}"
        )


def dbg_info_frame(frame: FrameType, name=None):
    if not name:
        logF.info(f"###'frame'.f_locals### = {str(frame.f_code)[13:]} \n   {frame.f_locals}")
    else:
        logF.info(f"###'frame'.f_locals### '{name}' \n   {frame.f_locals}")


def log_dict_items(log_dict: dict, descr="dict"):
    s = "\n".join([f"{k}: {v}" for k, v in log_dict.items() if k not in list_not])
    logF.info(f"log_dict_items : {descr} \n{s}")
