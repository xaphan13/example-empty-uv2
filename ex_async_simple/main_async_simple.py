from config_log import ConfigLogger

logF = ConfigLogger.get_logger("OnlyFile")

import asyncio

from ex_async_simple import (
    one_task_not_error,
    gather_demo,
    demo_context_var,
)


def run_simple_demo(w=None):
    if w is not None:  # w=None
        return
    logF.info(f"'****' run_simple_demo - 'start'")

    # asyncio.run(gather_demo.return_gather())
    # one_task_not_error.run_main_task()
    asyncio.run(demo_context_var.context_in_diff_tasks())
