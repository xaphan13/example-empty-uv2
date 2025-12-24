from config_log import ConfigLogger

logF = ConfigLogger.get_logger("OnlyFile")

from pathlib import Path


DIR_CWD: Path = Path.cwd()
DIR_CURRENT_FILE: Path = Path(__file__).resolve().parent

NAME_DIR_FILES: str = "zip_files_dir/"
DIR_FILES: Path = DIR_CURRENT_FILE / NAME_DIR_FILES


def log_paths():
    logF.info(f"Absolute paths: {DIR_CWD=} \n{DIR_CURRENT_FILE=}")
    logF.info(f"Absolute paths: {NAME_DIR_FILES=} \n{DIR_FILES=}")


log_paths()
