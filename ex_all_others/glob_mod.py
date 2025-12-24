from config_log import ConfigLogger

logF = ConfigLogger.get_logger("OnlyFile")


ggg = 1


def set_func(x):
    global ggg
    ggg = x


def get_func():
    global ggg
    return ggg
