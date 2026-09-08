from config_multi_proc_log import (
    multi_logger,
    main_process_start_logging,
    every_process_create_queue_handler,
)
from ex_work_process import multi_process_demo
from ex_work_process import pool_executor_demo
from ex_work_process import multi_pool_demo

logF = multi_logger


def run_process_demo(w=None):
    if w is not None:  # w=None
        return
    log_queue, listener = main_process_start_logging()  # Запускаем слушателя мультиОчереди логирования
    every_process_create_queue_handler(log_queue)

    logF.info(f"'****' run_process_demo - 'start'")

    multi_process_demo.start_process_demo(0)
    pool_executor_demo.run_executor_demo()
    multi_pool_demo.run_pool_demo(0)

    listener.stop()  # Останавливаем слушателя мультиОчереди логирования
