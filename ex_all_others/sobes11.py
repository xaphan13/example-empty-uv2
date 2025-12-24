from __future__ import annotations

from config_log import ConfigLogger

logF = ConfigLogger.get_logger("OnlyFile")


def get_first_match(predicate, objs=[]):
    match_obj = (obj for obj in objs if predicate(obj))
    logF.info(f"match_obj {match_obj}")
    # logF.info(f"match_obj {match_obj[0]}")  # TypeError: 'generator' object is not subscriptable
    logF.info(f"match_obj {next(match_obj)}")


def sob_work_1():
    logF.info(f"**** sob_work_1")

    logF.info(f"match_obj {sorted('Pythяon')[::-1]}")

    get_first_match(lambda o: o == 1, [1, 2, 3, 4])
    # get_first_match(lambda o: o == 1, [0, 2, 3, 4])  # сразу StopIteration - в пустом генераторе


# ------------------------------------------------------------------------
class A:
    def __init__(self):
        self.value = 5

    def __eq__(self, other):
        return self.value == other.value

    # def __hash__(self):  # TypeError: 'generator' object is not subscriptable
    #     if self.value == 5:
    #         return 1
    #     else:
    #         return 2


def not_hash_err():
    logF.info(f"'****' not_hash_err - 'start'")

    a = A()
    b = A()
    b.value = 10

    s = {a, b}
    logF.info(f"len {len(s)}")
