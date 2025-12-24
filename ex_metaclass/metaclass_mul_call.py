from config_log import ConfigLogger

logF = ConfigLogger.get_logger("OnlyFile")

from typing import Type


class DecorDescrLogger:
    def __init__(self, f):
        self.f = f

    def __get__(self, obj, objtype):
        logF.info(f"'Decor_descr_logger' call __get__() : {obj=}, \n{objtype=}")
        return self.f.__get__(obj, objtype)


# ------------------------------------------------------------------------
class MyMetaCls(type):
    def __call__(cls, *args, **kwargs):
        logF.info(f"Metaclass.__call__: {cls.__name__} : {args=} : {kwargs=}")
        result = super().__call__(*args, **kwargs)
        return result

    def __mul__(cls: Type["MyClassOne"], x: int) -> "MyClassOne":
        logF.info(f"'Metaclass.__mul__'(cls, x) : {x=}")
        return cls(x, "meta_mul")  # Создание и возврат экземпляра класса


class MyClassOne(metaclass=MyMetaCls):
    def __init__(self, x, name):
        logF.info(f"Class.__init__(self, x, name) {x=}, {name=}")
        self.x = x
        self.name = name

    def __call__(self, b: int):
        logF.info(f"{self.name} 'Class.__call__'(self, b: int); return int = {self.x=} + {b=}")
        new = self.x + b
        return new

    @DecorDescrLogger
    def __mul__(self, b: int):
        logF.info(f"{self.name} : 'Class.__mul__'(self, b: int); NEW : {self.x=} * {b=}")
        new = self.x * b
        return MyClassOne(new, "cls_mul")

    def __repr__(self):
        return f"MyDunder({self.name} = {self.x})"


def id_print_mull(x8):
    logF.info(f"'start' - id_print_mull\n")

    # 0. Получаем ID функции '__mul__' определённой в классе MyClass_1 через декоратор
    func = MyClassOne.__dict__.get("__mul__").f
    logF.info(f"ID function __mul__: {id(func)=}, {type(func)=}\n")

    # 1. Получаем ID и тип метода '__mul__' из словаря класса MyClass_1 (используя __dict__)
    # __dict__ содержит все атрибуты и методы класса - вернётся сам ДЕСКРИПТОР
    a = id(MyClassOne.__dict__.get("__mul__")), type(MyClassOne.__dict__.get("__mul__"))
    logF.info(f"ID : {a=}\n")

    # 2. Получаем ID и тип метода '__mul__' напрямую из самого класса MyClass_1
    # если не через __dict__ - то вернётся - сама ФУНКЦИЯ с параметром self
    b = id(MyClassOne.__mul__), type(MyClassOne.__mul__)
    logF.info(f"ID : {b=}\n")

    # 3. Получаем ID и тип метода '__mul__' через функцию 'getattr' для класса MyClass_1
    # 'getattr' позволяет получить атрибут по имени - вернётся - сама ФУНКЦИЯ с параметром self
    c = id(getattr(MyClassOne, "__mul__")), type(getattr(MyClassOne, "__mul__"))
    logF.info(f"ID : {c=}\n")

    # 4. Пробуем получаем ID и тип метода '__mul__' из словаря экземпляра (x8) класса
    # получаем NoneType - в словаре экземпляра НЕТ функций - они в классе только
    d = id(x8.__dict__.get("__mul__")), type(x8.__dict__.get("__mul__"))
    logF.info(f"ID : {d=}\n")

    # 5. Получаем ID и тип метода '__mul__' напрямую из экземпляра 'x8'
    # обращение к дескриптору в классе MyClass_1 - вернётся МЕТОД без параметра self
    e = id(x8.__mul__), type(x8.__mul__)
    logF.info(f"ID : {e=}\n")

    # 6. Получаем ID и тип метода '__mul__' из экземпляра 'x8' через функцию 'getattr'
    # обращение к дескриптору в классе MyClass_1 - вернётся МЕТОД без параметра self
    f = id(getattr(x8, "__mul__")), type(getattr(x8, "__mul__"))
    logF.info(f"ID : {f=}\n")


# ------------------------------------------------------------------------
def example_call_func_mul():
    # если поставить круглые скобки после класса MyClass_1 - то вызовется
    # метод __call__() определённый в МЕТА классе MyClass_1
    # это создаст экземпляр класса MyClass_1 и никакой магии:)
    x1 = MyClassOne(11, "x1")
    x2 = MyClassOne(22, "x2")
    logF.info(f"start - example_call_func_mul\n")

    # если поставить круглые скобки после экземпляра - то вызовется
    # метод __call__() определённый в классе MyClass_1
    x3 = x2(11)  # сахар для вызова __call__() из класса MyClass_1 - как ниже
    # x3 = x2.__call__(11)
    # x3 = MyClass_1.__call__(x2, 11)
    logF.info(f"after : [x3 = x2(2)] -> {x2=} & {x3=}\n")

    # знак умножения после класса вызывает метод __mul__() из метакласса
    # Использование __mul__ определённого в metaclass = MyMeta_1
    x4 = MyClassOne * 44
    logF.info(f"after : [x4 = MyClass_1 * 44] -> {x4=}\n")

    # знак умножения после экземпляра класса - вызывает метод __mul__() из класса
    # Использование __mul__ определённого в классе = MyClass_1
    x5 = x1 * 5
    logF.info(f"after : [x5 = x1 * 5] -> {x2=} & {x5=}\n")

    # обращение к дескриптору в классе MyClass_1 = [ __mul__.__get__(x1, MyClass_1) ]
    # ВЕРНЁТ =  [def __mul__(b: int):]
    x6 = x1.__mul__(6)
    logF.info(f"after : [x6 = x1.__mul__(6)] -> {x1=} & {x6=}\n")  # Использование __mul__

    # дескриптор __mul__.__get__() : ВЕРНЁТ =  [def __mul__(self, b: int):]
    x7 = MyClassOne.__mul__(x1, 7)
    logF.info(f"after : [x7 = MyClass_1.__mul__(x1, 7)] -> {x7=}\n")  # Использование __mul__

    # __dict__.get("__mul__") : ВЕРНЁТ = дескриптор __mul__
    # далее вызов __get__() : ВЕРНЁТ =  [def __mul__(b: int):]
    x8 = MyClassOne.__dict__.get("__mul__").__get__(x2, MyClassOne)(9)
    logF.info(f"after : [x8 = MyClass_1.__mul__(x2, 9)] -> {x8=}\n")  # Использование __mul__

    # id_print_mull(x8)


# ------------------------------------------------------------------------
def mul_func_descriptor():
    logF.info(f"'****' mul_func_descriptor - 'start'")

    example_call_func_mul()
