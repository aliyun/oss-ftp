#!/usr/bin/env python
# coding:utf-8

import os, sys
import time
import atexit
import webbrowser
import launcher_log

current_path = os.path.dirname(os.path.abspath(__file__))
root_path = os.path.abspath( os.path.join(current_path, os.pardir))
if root_path not in sys.path:
    sys.path.append(root_path)

has_desktop = True
if sys.platform.startswith("linux"):
    python_lib_path = os.path.abspath( os.path.join(root_path, "python27", "unix", "lib"))
    sys.path.append(python_lib_path)
    from ossftp.ftpd import FTPd

    def X_is_running():
        try:
            from subprocess import Popen, PIPE
            p = Popen(["xset", "-q"], stdout=PIPE, stderr=PIPE)
            p.communicate()
            return p.returncode == 0
        except:
            return False

    if X_is_running():
        from gtk_tray import sys_tray
    else:
        from non_tray import sys_tray
        has_desktop = False

elif sys.platform == "win32":
    from win_tray import sys_tray
    from ossftp.ftpd import FTPd
elif sys.platform == "darwin":
    python_lib_path = os.path.abspath( os.path.join(root_path, "python27", "unix", "lib"))
    sys.path.append(python_lib_path)
    extra_lib = "/System/Library/Frameworks/Python.framework/Versions/2.7/Extras/lib/python/PyObjc"
    sys.path.append(extra_lib)
    from ossftp.ftpd import FTPd

    try:
        import mac_tray as sys_tray
    except:
        from non_tray import sys_tray
else:
    print("detect platform fail:%s" % sys.platform)
    from non_tray import sys_tray
    has_desktop = False

import config
import web_control
import module_init

def exit_handler():
    print 'Stopping all modules before exit!'
    module_init.stop_all()
    web_control.stop()

atexit.register(exit_handler)




def main():

    # change path to launcher
    global __file__
    __file__ = os.path.abspath(__file__)
    if os.path.islink(__file__):
        __file__ = getattr(os, 'readlink', lambda x: x)(__file__)
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    web_control.confirm_ossftp_exit()

    module_init.start_all_auto()

    web_control.start()


    if has_desktop and config.get(["modules", "launcher", "popup_webui"], 1) == 1:
        webbrowser.open("http://127.0.0.1:8192/")

    if config.get(["modules", "launcher", "show_systray"], 1):
        sys_tray.serve_forever()
    else:
        while True:
            time.sleep(100)

    module_init.stop_all()
    sys.exit()



if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt: # Ctrl + C on console
        module_init.stop_all()
        sys.exit
