from config_log import ConfigLogger

logF = ConfigLogger.get_logger("OnlyFile")

import re


def split_for(s):
    if len(s) % 2 != 0:
        s += "_"

    # Нарезаем строку кусочками по два символа
    return [s[i : i + 2] for i in range(0, len(s), 2)]


def split_re(s):
    if len(s) % 2 != 0:
        s += "_"

    # Используем регулярные выражения для разделения строки на блоки длиной 2 символа
    return re.findall(r".{2}", s)


def split_zip_map(s):
    extended_s = s + ("_" if len(s) % 2 else "")

    iterator = iter(extended_s)
    # Применяем zip(), объединяя элементы по двое.
    # Преобразуем кортежи обратно в строки.
    return list(map("".join, zip(iterator, iterator)))


def run_split_strings():
    logF.info(f"'****' run_split_strings - 'start'")

    s1 = "abc"
    s2 = "abcdef"
    s3 = "abcdefghijklmnopqrstuvwxyz"

    # logF.info(f"s1 - for {split_for(s1)}")
    # logF.info(f"s2 - for {split_for(s2)}")
    # logF.info(f"s1 - re  {split_re(s1)}")
    # logF.info(f"s2 - re  {split_re(s2)}")
    logF.info(f"s1 - map  {split_zip_map(s1)}")
    logF.info(f"s2 - map  {split_zip_map(s2)}")
    logF.info(f"s3 - map  {split_zip_map(s3)}")
