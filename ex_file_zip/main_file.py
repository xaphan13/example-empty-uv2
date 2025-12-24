from config_log import ConfigLogger

logF = ConfigLogger.get_logger("OnlyFile")

from ex_file_zip import simple_zip
from ex_file_zip import zip_no_temp
from ex_file_zip import zip_read_extract


def run_file_zip(w=None):
    if w is not None:  # w=None
        return
    logF.info(f"'****' main_file_zip - 'start'")

    simple_zip.write_to_zip()
    zip_no_temp.write_to_zip_no_temp()
    zip_read_extract.read_extract_from_zip()
