from config_multi_proc_log import (
    multi_logger,
    main_process_start_logging,
    every_process_create_queue_handler,
)

logF = multi_logger

from ex_work_process import demo_class_process


def run_process_demo(w=None):
    if w is not None:  # w=None
        return
    log_queue, listener = main_process_start_logging()  # Запускаем слушателя мультиОчереди логирования
    every_process_create_queue_handler(log_queue)

    logF.info(f"'****' run_process_demo - 'start'")

    demo_class_process.two_class_proc()

    listener.stop()  # Останавливаем слушателя мультиОчереди логирования
