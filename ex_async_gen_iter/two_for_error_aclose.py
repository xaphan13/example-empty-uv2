from config_log import ConfigLogger

logF = ConfigLogger.get_logger("OnlyFile")

import asyncio
import contextlib

from typing import AsyncGenerator


work_done = False


async def cursor() -> AsyncGenerator[int, None]:
    try:
        print(asyncio.current_task().get_name())
        yield 1
    finally:
        print(asyncio.current_task().get_name())
        assert work_done
        print(work_done)


async def rows() -> AsyncGenerator[int, None]:
    global work_done
    try:
        print(asyncio.current_task().get_name())
        yield 2
        yield 3
    finally:
        print([t.get_name() for t in asyncio.all_tasks()])
        print(asyncio.current_task().get_name())
        await asyncio.sleep(0.1)  # imitate some async work
        work_done = True


async def two_async_for_err():
    async for c in cursor():
        print(c)
        gg: AsyncGenerator[int, None] = rows()
        async for r in gg:
            print(r)
            # await gg.aclose()  # вместо break - тогда без ошибок
            break
        break
    print(asyncio.current_task().get_name())
    print([t.get_name() for t in asyncio.all_tasks()])
    await asyncio.sleep(0.1)
    print([t.get_name() for t in asyncio.all_tasks()])


async def two_async_for():
    async with contextlib.aclosing(cursor()) as cursor_gen:
        async for c in cursor_gen:
            print(c)
            async with contextlib.aclosing(rows()) as rows_gen:
                async for r in rows_gen:
                    print(r)
                    break
            break
        print(asyncio.current_task().get_name())
        print([t.get_name() for t in asyncio.all_tasks()])
        await asyncio.sleep(0.1)
        print([t.get_name() for t in asyncio.all_tasks()])
