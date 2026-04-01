from config_log import ConfigLogger

logF = ConfigLogger.get_logger("OnlyFile")

import asyncio

from ex_async_with import demo_create_session


def run_with_demo(w=None):
    if w is not None:  # w=None
        return
    logF.info(f"'****' run_with_demo - 'start'")

    asyncio.run(demo_create_session.run_demo_simple())
