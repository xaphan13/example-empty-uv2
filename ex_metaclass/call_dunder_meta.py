from __future__ import annotations

from config_log import ConfigLogger

logF = ConfigLogger.get_logger("OnlyFile")


class MyMeta(type):
    def __call__(cls: "MyClass", *args, **kwargs) -> "MyClass":
        logF.info(f"MyMeta.__call__: {cls.__name__} : {args=} : {kwargs=}")
        return super().__call__(*args, **kwargs)

    def __add__(cls: "MyClass", other: int) -> "MyClass":
        logF.info(f"MyMeta.__add__: {cls.__name__} : {other=}")
        return cls(other + other)


class MyClass(metaclass=MyMeta):
    def __init__(self, x: int):
        self.x = x

    def __call__(self, other: int) -> MyClass:
        logF.info(f"MyClass.__call__: {self.x=} : {other=}")
        return MyClass(self.x + other)

    def __add__(self, other: int | MyClass) -> MyClass:
        if isinstance(other, MyClass):
            logF.info(f"MyClass.__add__: {self.x=} : {other.x=}")
            return MyClass(self.x + other.x)
        logF.info(f"MyClass.__add__: {self.x=} : {other=}")
        return MyClass(self.x + other)


def run_call_dunder_meta():
    logF.info(f"run_call_dunder_meta - 'start'\n")

    inst_meta_call = MyClass(0)
    logF.info(f"'inst_meta_call = MyClass(1)' '-->>' {inst_meta_call=}")
    inst_meta_add = MyClass + 2
    logF.info(f"'inst_meta_add = MyClass + 2' '-->>' {inst_meta_add=}\n")

    inst = MyClass(1)
    logF.info(f"'inst' '----------------------------------->>' {inst=}\n")

    inst_cls_call = inst(10)
    logF.info(f"'inst_cls_call = a(10)' '-->>' {inst_cls_call=}")
    inst_cls_add = inst + 100
    logF.info(f"'inst_cls_add = a + 100' '-->>' {inst_cls_add=}\n")

    func_call_cls = MyClass.__call__
    logF.info(f"'func_call_cls = MyClass.__call__' '-->>' {func_call_cls=}")
    func_add_cls = MyClass.__add__
    logF.info(f"'func_add_cls = MyClass.__add__' '-->>' {func_add_cls=}\n")

    method_call_bound_inst = inst.__call__
    logF.info(f"'method_call_bound_inst = a.__call__' '-->>' {method_call_bound_inst=}\n")

    method_call_bound_get = MyClass.__call__.__get__(inst)
    logF.info(f"'MyClass.__call__.__get__(inst)'       '-->>' {method_call_bound_get=}\n")

    method_add_bound_inst = inst.__add__
    logF.info(f"'method_add_bound_inst = a.__call__'    '-->>' {method_add_bound_inst=}\n")

    method_add_bound_get = MyClass.__add__.__get__(inst)
    logF.info(f"'MyClass.__add__.__get__(inst)'          '-->>' {method_add_bound_get=}\n")

    func_call_cls(inst, 30)
    func_add_cls(inst, 300)
    method_call_bound_inst(20)
    method_add_bound_inst(200)
    logF.info(f"--------------------------------\n")

    inst_double_add_int = inst + 400 + 400
    logF.info(f"'inst_double_add_int = a + 400 + 400' '-->>' {inst_double_add_int=}\n")

    inst_double_add_inst = inst + 500 + inst
    logF.info(f"'inst_double_add_inst = a + 500 + 500' '-->>' {inst_double_add_inst=}\n")
