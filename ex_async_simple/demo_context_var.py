from config_log import ConfigLogger

logF = ConfigLogger.get_logger("OnlyFile")

import asyncio
from contextvars import ContextVar, copy_context


cont_var = ContextVar("cont_var", default="default")


async def fun_cor_task_2(name: str):
    val_2 = cont_var.get()
    logF.info(f"{name}: cont_var= {val_2}")
    await asyncio.sleep(0.1)
    cont_var.set("set in task-2")
    print_context(name)


async def fun_cor_task_3(name: str):
    val_3 = cont_var.get()
    logF.info(f"{name}: cont_var= {val_3}")
    await asyncio.sleep(0.1)
    cont_var.set("set in task-3")
    print_context(name)


def print_context(name: str):
    ctx = copy_context()
    for var, value in ctx.items():
        logF.warn(f"{name} ->'copy_context' : {var.name} = {value}")


async def context_in_diff_tasks():
    cont_var.set("val-1")
    print_context("MAIN")

    cor_2 = fun_cor_task_2("task-2")
    cont_var.set("val-2")
    task_2 = asyncio.create_task(cor_2)

    cor_3 = fun_cor_task_3("task-3")
    cont_var.set("val-3")
    task_3 = asyncio.create_task(cor_3)

    cont_var.set("val-4")
    print_context("MAIN")

    await task_2
    await task_3
    print_context("MAIN")
