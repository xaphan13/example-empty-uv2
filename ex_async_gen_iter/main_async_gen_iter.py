from config_log import ConfigLogger

logF = ConfigLogger.get_logger("OnlyFile")

import asyncio

from ex_async_gen_iter import (
    demo_anext_asend,
    two_for_error_aclose,
)


def run_gen_iter_demo(w=None):
    if w is not None:  # w=None
        return
    logF.info(f"'****' run_gen_iter_demo - 'start'")

    # asyncio.run(two_for_error_aclose.two_async_for_err())
    # asyncio.run(two_for_error_aclose.two_async_for())
    asyncio.run(demo_anext_asend.run_anext_err())
