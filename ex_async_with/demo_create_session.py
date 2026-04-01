from config_log import ConfigLogger

logF = ConfigLogger.get_logger("OnlyFile")

import asyncio

from ex_async_with.with_connection_factory import ConnectionHelper


async def run_demo_simple():
    logF.info(f"run_demo_simple")
    async with ConnectionHelper("localhost", 9001) as conn:
        logF.info(f"after 'WITH'")
        send_task = asyncio.create_task(conn.send())
        recv_task = asyncio.create_task(conn.recv())
        await send_task
        await recv_task
