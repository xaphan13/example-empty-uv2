from config_log import ConfigLogger

logF = ConfigLogger.get_logger("OnlyFile")

from ex_code_war import split_strings
from ex_code_war import iadd_demo
from ex_code_war import valid_bracket


# ------------------------------------------------------------------------
def code_war_1(w=None):
    if w is not None:  # w=None
        return
    logF.info(f"'****' main_code_war - 'start'")

    # iadd_demo.run_iadd_demo()
    # split_strings.run_split_strings()
    valid_bracket.run_valid()
