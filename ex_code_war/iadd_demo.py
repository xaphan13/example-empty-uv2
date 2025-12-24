from config_log import ConfigLogger

logF = ConfigLogger.get_logger("OnlyFile")


def run_iadd_demo():
    logF.info(f"'****' run_iadd_demo - 'start'")

    print(10 or 5 * 7)

    a = [1, 2, 3]
    b = [4, 5, 6]
    print(f"{id(a)} - {id(b)}")

    # a = a + b
    # a = a.__add__(b)
    # a += b
    # a.__iadd__(b)
    # a + b
    # a.__add__(b)

    b = a.__iadd__(b)
    print(f"{id(a)} - {id(b)}")
    print(a)
