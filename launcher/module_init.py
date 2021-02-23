import subprocess
import threading
import launcher_log
import os
import sys
import config


import web_control
import time
proc_handler = {}


current_path = os.path.dirname(os.path.abspath(__file__))
root_path = os.path.abspath( os.path.join(current_path, os.pardir))
if root_path not in sys.path:
    sys.path.append(root_path)


def start(module):
    if not os.path.isdir(os.path.join(root_path, module)):
        return

    try:
        if not module in config.config["modules"]:
            launcher_log.error("module not exist %s", module)
            raise

        if module in proc_handler:
            launcher_log.error("module %s is running", module)
            return "module is running"

        if module not in proc_handler:
            proc_handler[module] = {}

        if module == 'ossftp':
            enable = config.get(["modules", "ossftp", "enable"], 1)
            if enable == 0:
                launcher_log.info("ossftp has not configured enable, so it didn't start.")
                return "fail"
            masquerade_address = config.get(["modules", "ossftp", "masquerade_address"], "")
            address = config.get(["modules", "ossftp", "address"], "127.0.0.1")
            port = config.get(["modules", "ossftp", "port"], 2048)
            passive_ports_start = config.get(["modules", "ossftp", "passive_ports_start"], 51000)
            passive_ports_end = config.get(["modules", "ossftp", "passive_ports_end"], 53000)
            is_internal = config.get(["modules", "ossftp", "internal"], None)
            log_level = config.get(["modules", "ossftp", "log_level"], "INFO")
            bucket_endpoints = config.get(["modules", "ossftp", "bucket_endpoints"], "")

            buff_size = config.get(["modules", "ossftp", "buff_size"], 10)
            protocol = config.get(["modules", "launcher", "oss_protocol"], 'https')
            script_path = os.path.join(root_path, 'ossftp', 'ftpserver.py')
            if not os.path.isfile(script_path):
                launcher_log.critical("start module script not exist:%s", script_path)
                return "fail"

            cmd = [sys.executable, script_path, "--listen_address=%s"%address, "--port=%d"%port, "--passive_ports_start=%d"%passive_ports_start,
                "--passive_ports_end=%d"%passive_ports_end,"--loglevel=%s"%log_level, "--bucket_endpoints=%s"%bucket_endpoints, "--buff_size=%d"%buff_size, "--protocol=%s" % protocol]
            print(cmd)
            proc_handler[module]["proc"] = subprocess.Popen(cmd, shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        elif module == 'osssftp':
            enable = config.get(["modules", "osssftp", "enable"], 0)
            if enable == 0:
                launcher_log.info("osssftp has not configured enable, so it didn't start.")
                return "fail"
            address = config.get(["modules", "osssftp", "address"], "127.0.0.1")
            port = config.get(["modules", "osssftp", "port"], 50000)
            is_internal = config.get(["modules", "osssftp", "internal"], None)
            log_level = config.get(["modules", "osssftp", "log_level"], "INFO")
            bucket_endpoints = config.get(["modules", "osssftp", "bucket_endpoints"], "")
            buff_size = config.get(["modules", "osssftp", "buff_size"], 10)
            protocol = config.get(["modules", "launcher", "oss_protocol"], 'https')
            script_path = os.path.join(root_path, 'osssftp', 'sftpserver.py')
            if not os.path.isfile(script_path):
                launcher_log.critical("start module script not exist:%s", script_path)
                return "fail"
            cmd = [sys.executable, script_path, "--listen_address=%s" % address, "--port=%d" % port, "--loglevel=%s" % log_level,
                   "--bucket_endpoints=%s" % bucket_endpoints, "--buff_size=%d" % buff_size, "--protocol=%s" % protocol]
            print(cmd)
            proc_handler[module]["proc"] = subprocess.Popen(cmd, shell=False, stdout=subprocess.PIPE,
                                                            stderr=subprocess.PIPE)
        else:
            raise ValueError("Wrong module: %s" % module)
        
        launcher_log.info("%s started", module)

    except Exception as e:
        launcher_log.exception("start module %s fail:%s", module, e)
        return "Except:%s" % e
    return "start success."

def stop(module):
    try:
        if not module in proc_handler:
            launcher_log.error("module %s not running", module)
            return
        if proc_handler[module].get('proc') is not None:
            proc_handler[module]["proc"].terminate()  # Sends SIGTERM
            proc_handler[module]["proc"].wait()

        del proc_handler[module]

        launcher_log.info("module %s stopped", module)
    except Exception as e:
        launcher_log.exception("stop module %s fail:%s", module, e)
        return "Except:%s" % e
    return "stop success."

def start_all_auto():
    for module in config.config["modules"]:
        if module == "launcher":
            continue

        start_time = time.time()
        ret = start(module)
        if ret == "fail":
            continue

        #web_control.confirm_module_ready(config.get(["modules", module, "control_port"], 0))
        finished_time = time.time()
        launcher_log.info("start %s time cost %d", module, (finished_time - start_time) * 1000)

def stop_all():
    running_modules = [k for k in proc_handler]
    for module in running_modules:
        stop(module)

