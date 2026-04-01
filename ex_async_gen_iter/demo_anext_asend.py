from typing import Awaitable

from config_log import ConfigLogger

logF = ConfigLogger.get_logger("OnlyFile")

import asyncio


async def gen_with_asend():
    message = yield 1
    logF.info(f"received = {message}")
    await asyncio.sleep(0.1)

    message = yield 2
    logF.info(f"received = {message}")


async def fun_cor_asend_err(asend: Awaitable[int]):
    logF.info(f"'task' {asyncio.current_task().get_name()} = {asend}")
    res: int = await asend
    logF.info(f"'task' {asyncio.current_task().get_name()} : await result : {res=}")
    return res


def handle_task_result(task: asyncio.Task):
    try:
        res = task.result()  # выбросит исключение, если оно было
        logF.warn(f"done_callback {task.get_name()} : Result= {res}")
    except RuntimeError as e:
        logF.error(f"done_callback {task.get_name()} : Exception= {e}")


async def run_anext_err():
    agen = gen_with_asend()
    # await agen.asend(None)

    return_next: Awaitable[int] = anext(agen)

    first = await return_next
    logF.info(f"result : {first=}")

    asend_a: Awaitable[int] = agen.asend("A")
    asend_b: Awaitable[int] = agen.asend("B")

    task_2 = asyncio.create_task(fun_cor_asend_err(asend_a))
    task_2.add_done_callback(handle_task_result)

    task_3 = asyncio.create_task(fun_cor_asend_err(asend_b))
    task_3.add_done_callback(handle_task_result)

    res_task_2 = await task_2
    logF.info(f"'main task' {asyncio.current_task().get_name()} : Result= {res_task_2=}")

    try:
        res_task_3 = await task_3
        logF.info(f"'main task' {asyncio.current_task().get_name()} : {res_task_3=}")
    except RuntimeError as e:
        logF.error(f"await {task_3.get_name()} : Exception= {e}")
