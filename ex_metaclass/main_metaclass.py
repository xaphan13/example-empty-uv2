from config_log import ConfigLogger

logF = ConfigLogger.get_logger("OnlyFile")

from ex_metaclass import metaclass_mul_call
from ex_metaclass import call_dunder_meta
from ex_metaclass import vars_inside_func


# ------------------------------------------------------------------------
def main_metaclass(w=None):
    if w is not None:  # w=None
        return
    logF.info(f"'****' main_metaclass - 'start'")

    # from ex_metaclass import noisy_meta
    # noisy_meta.start_noisy_meta()

    # metaclass_mul_call.mul_func_descriptor()
    # call_dunder_meta.run_call_dunder_meta()
    vars_inside_func.run_demo()
