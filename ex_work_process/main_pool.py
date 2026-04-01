from config_multi_proc_log import (
    multi_logger,
    main_process_start_logging,
    every_process_create_queue_handler,
)

logF = multi_logger

from ex_work_process import pool_demo


def main():
    """
    Главная точка входа для демонстрации пула процессов.
    Создает слушателя логов, настраивает логирование для главного процесса
    и запускает демонстрацию.
    """
    # Запускаем слушателя мультиОчереди логирования для сбора логов со всех процессов
    log_queue, listener = main_process_start_logging()

    # Настраиваем обработчик логов для главного процесса
    every_process_create_queue_handler(log_queue)

    logF.info("==== Starting Pool Demo Main ====")

    try:
        # Запускаем новую демонстрацию
        pool_demo.run_pool_demo()
    except Exception as e:
        logF.error(f"Error in main_pool: {e}")
    finally:
        logF.info("==== Finished Pool Demo Main ====")
        # Останавливаем слушателя логов, чтобы программа могла корректно завершиться
        listener.stop()


if __name__ == "__main__":
    main()
