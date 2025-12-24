from config_log import ConfigLogger

logF = ConfigLogger.get_logger("OnlyFile")

from dis import dis
import asyncio

from typing import Any, Coroutine
from asyncio import Task


async def fun_cor1(x):
    logF.info(f"fun_cor1 - старт = {x}")
    await asyncio.sleep(0)
    logF.info(f"fun_cor1 - середина = {x}")
    await asyncio.sleep(0)
    logF.info(f"fun_cor1 - завершена = {x}")


async def run_cor():
    # logF.info(f"run_cor - RUN")

    cor: Coroutine[Any, Any, None] = fun_cor1(4)
    await cor
    task: Task[None] = asyncio.create_task(fun_cor1(7))
    await task


def async_start():
    logF.info(f"'****' async_start - 'start'")

    dis(run_cor)

    # cor = fun_cor1(4)
    asyncio.run(run_cor())
