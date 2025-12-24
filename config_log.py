import logging.config
import os


LOG_DIR = "./log"
LOG_FILE = "example.log"


class ConfigLogger:
    pathLoggerDir = LOG_DIR
    nameFileLogger = LOG_FILE
    isSetting = False  # для того чтобы settingLogger() вызвать один раз при запуске программы

    @staticmethod
    def __create_log_dir(pathDir):
        """Создание папки для лог-файлов"""
        if not os.path.exists(pathDir):
            os.mkdir(pathDir)

    @staticmethod
    def __settings_logger(log_dir=pathLoggerDir, log_file=nameFileLogger):
        """настройка логгера с использованием словаря"""
        ConfigLogger.__create_log_dir(pathDir=log_dir)

        logging_config = create_config_dict(log_dir, log_file)
        logging.config.dictConfig(logging_config)

        logging.basicConfig(level=logging.INFO, handlers=[])
        ConfigLogger.isSetting = True

    @staticmethod
    def setting_path_logger(log_dir=LOG_DIR, log_file=LOG_FILE):
        """настройка имени файла логгера и директории"""
        ConfigLogger.pathLoggerDir = log_dir
        ConfigLogger.nameFileLogger = log_file
        ConfigLogger.__settings_logger(log_dir, log_file)

    @staticmethod
    def get_logger(nameBase):
        """nameBase берётся из словаря = 'loggers'
        OnlyFile = логгер будет писать в файл, в консоль не будет
        Stdout = только в консоль; FileStdout = и в консоль и в файл
        """
        if not ConfigLogger.isSetting:
            ConfigLogger.__settings_logger()
        return logging.getLogger(nameBase)


def create_config_dict(pathLoggerDir, nameFileLogger):
    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "form1": {
                "format": "/* %(asctime)s - %(module)s.%(funcName)s(%(lineno)d) - [%(threadName)s] - %(thread)d - [%(processName)s] - %(process)d */ -> \n%(levelname)s: %(message)s"
            },
            "form2": {
                "format": "/* %(asctime)s - %(module)s.%(funcName)s(%(lineno)d) - [%(threadName)s] - [%(thread)d] */  \n%(levelname)s: %(message)s"
            },
            "form3": {
                "format": "/* %(asctime)s - %(module)s.%(funcName)s(%(lineno)d) - %(name)s */ -> \n%(levelname)s: %(message)s"
            },
            "form4": {
                "format": "/* %(asctime)s - %(module)s.%(funcName)s(%(lineno)d) - [%(processName)s] - %(process)d */ -> \n%(levelname)s: %(message)s"
            },
            "con1": {
                "format": "%(asctime)s - %(module)s.%(funcName)s(%(lineno)d) - [%(threadName)s] - [%(thread)d] \n > %(levelname)s: %(message)s"
            },
            "con2": {
                "format": "%(asctime)s - %(module)s.%(funcName)s(%(lineno)d) - [%(threadName)s] - [%(thread)d] > %(levelname)s: %(message)s"
            },
        },
        "handlers": {
            "rotating_file1": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "INFO",
                "formatter": "form2",
                "filename": f"{pathLoggerDir}/{nameFileLogger}",
                "maxBytes": 1048576,
                "backupCount": 20,
            },
            "console1": {
                "class": "logging.StreamHandler",
                "level": "INFO",
                "formatter": "con2",
                "stream": "ext://sys.stdout",
            },
        },
        "loggers": {
            "Stdout": {"handlers": ["console1"], "level": "DEBUG"},
            "FileStdout": {
                "handlers": ["rotating_file1", "console1"],
                "level": "DEBUG",
            },
            "OnlyFile": {"handlers": ["rotating_file1"], "level": "DEBUG"},
        },
    }

    return logging_config
