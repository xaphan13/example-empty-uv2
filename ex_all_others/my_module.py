from config_log import ConfigLogger as logger
import config_log as config


class MyClass:
    attr = 1

    def __init__(self, param):
        self.name_attr = param

    def get_name(self):
        return self.name_attr


obj = MyClass("Hello")

obj.get_name()
MyClass.get_name(obj)

a = obj.get_name
b = MyClass.get_name

a()
