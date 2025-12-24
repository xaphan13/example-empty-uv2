from config_log import ConfigLogger

logF = ConfigLogger.get_logger("OnlyFile")


def isValid1(s):
    rs = s
    while "()" in s or "{}" in s or "[]" in s:
        s = s.replace("()", "").replace("{}", "").replace("[]", "")
    return s == "", rs


def isValid(s):
    rs = s
    depot = []
    mapping = {")": "(", "}": "{", "]": "[", "(": "", "{": "", "[": ""}
    if len(s) % 2 != 0 or mapping.get(s[0]):
        return False, rs

    for char in s:
        a = mapping.get(char)
        if not a:
            depot.append(char)
        else:
            if (last := depot.pop()) != a:
                return False, last, a

    if depot:
        return False, rs
    return True, rs


def run_valid():
    logF.info(f"'****' run_valid - 'start'")

    logF.info(f"inn() - res = {isValid('({[]})')}")
    logF.info(f"inn() - res = {isValid('({[]})')}")
    logF.info(f"inn() - res = {isValid('([)]')}")
