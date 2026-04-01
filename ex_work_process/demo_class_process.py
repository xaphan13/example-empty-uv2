from time import sleep

from config_multi_proc_log import (
    multi_logger,
    logger_settings,
)

logF = multi_logger

from multiprocessing import Queue

from ex_work_process.work_class_process import Process_work


def two_class_proc():
    logF.info(f"'****' two_class_proc - 'start'")

    inqueue, outqueue = Queue(), Queue()

    prc1 = Process_work(logger_settings.get_queue(), inqueue, outqueue, name="NAME1")
    prc2 = Process_work(logger_settings.get_queue(), inqueue, outqueue, name="NAME2")

    prc1.start()
    prc2.start()
    sleep(0.5)
    logF.info(f"after starting process = \n{prc1}\n{prc2}")

    # ------------------------------------------------------------------------
    inqueue.put({"task": "1", "prc": "1"})
    inqueue.put({"task": "2", "prc": "2"})
    inqueue.put({"task": "3", "prc": "1"})
    inqueue.put({"task": "4", "prc": "2"})

    # ------------------------------------------------------------------------
    sleep(3)
    inqueue.put(prc1.STOP_SIGNAL)
    inqueue.put(prc2.STOP_SIGNAL)

    prc1.join()
    prc2.join()
