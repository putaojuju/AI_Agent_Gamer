# -*- coding: utf-8 -*-
import win32gui

windows = []

def callback(hwnd, param):
    try:
        title = win32gui.GetWindowText(hwnd)
        if title:
            windows.append((hwnd, title))
    except:
        pass

win32gui.EnumWindows(callback, None)

print('找到的窗口:')
for hwnd, title in windows[:30]:
    print(f'  {hwnd}: {title}')
