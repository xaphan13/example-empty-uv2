from config_log import ConfigLogger

logF = ConfigLogger.get_logger("OnlyFile")

import asyncio


flag = False


async def inner():
    global flag
    try:
        return
    finally:
        await asyncio.sleep(0)
        flag = True


async def outer():
    try:
        await inner()
    finally:
        print("flag =", flag)


def run_main_task():
    asyncio.run(outer())
