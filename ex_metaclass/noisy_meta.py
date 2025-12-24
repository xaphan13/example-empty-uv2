from config_log import ConfigLogger

logF = ConfigLogger.get_logger("OnlyFile")


logF.info(f"'<<<Beginning : MODULE'>>>")


class NoisyMeta(type):
    logF.info(f"<<<Beginning META of NoisyMeta class definition>>>")

    @classmethod
    def __prepare__(meta, name, bases):
        logF.info("'META function': __prepare__()")
        logF.info(f"Preparing: {meta=} {name=} {bases=}")
        result_prepare = super().__prepare__(name, bases)
        logF.info(f"{result_prepare=}")
        return result_prepare

    def __new__(mcs, name, bases, attrs):
        logF.info(f"'META function': __new__()")
        logF.info(f"Creating: {mcs=} {name=} {bases=}\n {attrs=}")
        result_new = super().__new__(mcs, name, bases, attrs)
        logF.info(f"{result_new=}")
        return result_new

    def __init__(cls, name, bases, attrs):
        logF.info(f"'META function': __init__()")
        logF.info(f"Initializing: {cls=} {name=} {bases=}\n {attrs=}")
        result_init = super().__init__(name, bases, attrs)
        logF.info(f"{result_init=}")

    def __call__(cls, *args, **kwargs):
        logF.info(f"'META function': __call__() 'START'\n")
        logF.info(f"__call__: {cls=} {cls.__name__=} {args=} {kwargs=}")
        result_call = super().__call__(*args, **kwargs)
        logF.info(f"'META function': __call__() 'END'\n result = {result_call}\n")
        return result_call

    logF.info(f"<<<End META of NoisyMeta class definition>>>")


logF.info(f"'<<<after NoisyMeta definition : MODULE>>>'\n")


class MyClassNoisy(metaclass=NoisyMeta):
    logF.info(f"<<<Beginning of MyClassNoisy class definition>>>")

    def __new__(cls, *args, **kwargs):
        logF.info(f"'MyClassNoisy function' -->> __new__(cls, *args, **kwargs)")
        logF.info(f"{cls=}, {args=}, {kwargs=}")
        return super().__new__(cls)

    def __init__(self, field):
        logF.info(f"'MyClassNoisy function' -->> __init__(self, field) : {field=}")
        self.x = field
        logF.info(f"{self.__dict__=}")

    logF.info(f"<<<End of MyClassNoisy class definition>>>")


logF.info(f"'<<<End : MODULE'>>>\n")


def start_noisy_meta():
    logF.info(f"'****' start_noisy_meta - 'start'")
    obj = MyClassNoisy(5)
    logF.info(f"'MyClassNoisy(5)' -->> {obj=}")
