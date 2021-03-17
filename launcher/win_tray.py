#!/usr/bin/env python
# coding:utf-8


import os, sys

is_py2 = (sys.version_info[0] == 2)
if is_py2:
    python_dir = "python27"
    import _winreg as winreg
else:
    python_dir = "python36"
    import winreg

current_path = os.path.dirname(os.path.abspath(__file__))
python_path = os.path.abspath( os.path.join(current_path, os.pardir, python_dir, 'win32'))
win32_lib = os.path.abspath( os.path.join(python_path, 'lib', 'win32'))
if win32_lib not in sys.path:
    sys.path.append(win32_lib)

import webbrowser
from systray import SysTrayIcon
import systray.win32_adapter as win32_adapter
import os
import ctypes
import win32_proxy_manager
import module_init

class Win_tray():
    def __init__(self):
        icon_path = os.path.join(os.path.dirname(__file__), "web_ui", "favicon.ico")
        self.systray = SysTrayIcon(icon_path, "OSS-FTP", self.make_menu(), self.on_quit, left_click=self.on_show, right_click=self.on_right_click)

        reg_path = r'Software\Microsoft\Windows\CurrentVersion\Internet Settings'
        self.INTERNET_SETTINGS = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
            reg_path,
            0, winreg.KEY_ALL_ACCESS)

    def get_proxy_state(self):
        REG_PATH = r'Software\Microsoft\Windows\CurrentVersion\Internet Settings'
        INTERNET_SETTINGS = winreg.OpenKey(winreg.HKEY_CURRENT_USER,REG_PATH,0, winreg.KEY_ALL_ACCESS)
        try:
            AutoConfigURL, reg_type = winreg.QueryValueEx(INTERNET_SETTINGS, 'AutoConfigURL')
            if AutoConfigURL:
                return "auto"
        except Exception as e:
            pass

        try:
            ProxyEnable, reg_type = winreg.QueryValueEx(INTERNET_SETTINGS, 'ProxyEnable')
            if ProxyEnable:
                return "enable"
        except Exception as e:
            pass
        return "disable"

    def on_right_click(self):
        self.systray.update(menu=self.make_menu())
        self.systray._show_menu()

    def make_menu(self):
        import locale
        lang_code, code_page = locale.getdefaultlocale()

        proxy_stat = self.get_proxy_state()
        enable_checked = win32_adapter.fState.MFS_CHECKED if proxy_stat=="enable" else 0
        auto_checked = win32_adapter.fState.MFS_CHECKED if proxy_stat=="auto" else 0   

        if lang_code == "zh_CN":
            menu_options = ((u"设置", None, self.on_show, 0),
                        (u"重启 OSS Ftp 代理服务器", None, self.on_restart_ossftp_proxy, 0))
        else:
            menu_options = ((u"Config", None, self.on_show, 0),
                        (u"Restart OSS Ftp Proxy", None, self.on_restart_ossftp_proxy, 0))
        return menu_options

    def on_show(self, widget=None, data=None):
        self.show_control_web()

    def on_restart_ossftp_proxy(self, widget=None, data=None):
        module_init.stop_all()
        module_init.start_all_auto()

    def on_check_update(self, widget=None, data=None):
        update.check_update()

    def show_control_web(self, widget=None, data=None):
        webbrowser.open("http://127.0.0.1:8192/")
        ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)

    def on_quit(self, widget, data=None):
        win32_proxy_manager.disable_proxy()

    def serve_forever(self):
        self.systray._message_loop_func()

    def dialog_yes_no(self, msg="msg", title="Title", data=None, callback=None):
        res = ctypes.windll.user32.MessageBoxW(None, msg, title, 1)
        # Yes:1 No:2
        if callback:
            callback(data, res)
        return res

sys_tray = Win_tray()

def main():
    ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)
    sys_tray.serve_forever()

if __name__ == '__main__':
    main()
