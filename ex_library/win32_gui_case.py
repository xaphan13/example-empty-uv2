from config_log import ConfigLogger

logF = ConfigLogger.get_logger("OnlyFile")

import win32gui
import win32con
import win32api
import time


def enum_windows():
    """Вернёт список (hwnd, title) всех видимых окон"""
    wins = []

    def callback(hwnd, _):
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd)
            if title:
                wins.append((hwnd, title))

    win32gui.EnumWindows(callback, None)
    return wins


def find_window_by_title_fragment(fragment):
    fragment = fragment.lower()
    for hwnd, title in enum_windows():
        if fragment in title.lower():
            return hwnd, title
    return None, None


def get_rect(hwnd):
    left, top, right, bottom = win32gui.GetWindowRect(hwnd)
    return left, top, right - left, bottom - top  # x, y, width, height


def set_size_and_pos(hwnd, x, y, width, height, topmost=False):
    flags = win32con.SWP_SHOWWINDOW
    if topmost:
        z = win32con.HWND_TOPMOST
    else:
        z = win32con.HWND_NOTOPMOST
    # SWP_FRAMECHANGED чтобы изменения стиля применились
    win32gui.SetWindowPos(hwnd, z, int(x), int(y), int(width), int(height), flags | win32con.SWP_FRAMECHANGED)


def remove_titlebar(hwnd):
    """Удаляет заголовок и рамки — окно станет фреймлес"""
    style = win32gui.GetWindowLong(hwnd, win32con.GWL_STYLE)
    # Убираем WS_CAPTION и WS_THICKFRAME (толстая рамка), можно убрать и другие флаги
    new_style = style & ~(win32con.WS_CAPTION | win32con.WS_THICKFRAME | win32con.WS_BORDER)
    win32gui.SetWindowLong(hwnd, win32con.GWL_STYLE, new_style)
    # Обновим оформление
    win32gui.SetWindowPos(
        hwnd,
        None,
        0,
        0,
        0,
        0,
        win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_NOZORDER | win32con.SWP_FRAMECHANGED,
    )


def restore_titlebar(hwnd, keep_thickframe=True):
    style = win32gui.GetWindowLong(hwnd, win32con.GWL_STYLE)
    style |= win32con.WS_CAPTION
    if keep_thickframe:
        style |= win32con.WS_THICKFRAME
    win32gui.SetWindowLong(hwnd, win32con.GWL_STYLE, style)
    win32gui.SetWindowPos(
        hwnd,
        None,
        0,
        0,
        0,
        0,
        win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_NOZORDER | win32con.SWP_FRAMECHANGED,
    )


def make_topmost(hwnd, enable=True):
    if enable:
        win32gui.SetWindowPos(hwnd, win32con.HWND_TOPMOST, 0, 0, 0, 0, win32con.SWP_NOMOVE | win32con.SWP_NOSIZE)
    else:
        win32gui.SetWindowPos(hwnd, win32con.HWND_NOTOPMOST, 0, 0, 0, 0, win32con.SWP_NOMOVE | win32con.SWP_NOSIZE)


def notepad_window():
    fragment = "блокнот"  # example — ищем окно по фрагменту заголовка
    fragment = "Подключение к удаленному рабочему столу"
    hwnd, title = find_window_by_title_fragment(fragment)

    if not hwnd:
        print("Окно не найдено")
        exit(1)

    x, y, w, h = get_rect(hwnd)
    print("Найдено:", hex(hwnd), title)
    print("Текущие координаты: ", x, y, w, h)

    # Пример: убираем заголовок, делаем окно 800x600 и ставим в позицию 100,100
    remove_titlebar(hwnd)
    time.sleep(0.05)  # небольшая пауза для применения (обычно не обязательна)
    # set_size_and_pos(hwnd, 0, 0, 2050, 1150, topmost=False)
    set_size_and_pos(hwnd, -6, -10, 2060, 1152, topmost=False)

    x, y, w, h = get_rect(hwnd)
    print("Изменено: ", x, y, w, h)

    # Если нужно вернуть:
    # restore_titlebar(hwnd)
    # make_topmost(hwnd, False)
