from config_log import ConfigLogger

logF = ConfigLogger.get_logger("OnlyFile")

from ex_library import streamz_from_iterable
from ex_library import my_stream_map
from ex_library import stream_example


# ------------------------------------------------------------------------
def main_library(w=None):
    if w is not None:  # w=None
        return
    logF.info(f"'****' main_library - 'start'")

    # streamz_from_iterable.run_streamz_example()
    # streamz_from_iterable.run_streamz_example_1()
    # streamz_from_iterable.run_streamz_example_2()

    # my_stream_map.chain_maps()
    stream_example.run_my_stream_example()
