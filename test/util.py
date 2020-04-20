# -*- coding: utf-8 -*-

import os
import sys
import platform
current_path = os.path.dirname(os.path.abspath(__file__))
root_path = os.path.abspath(os.path.join(current_path, os.pardir))
if root_path not in sys.path:
    sys.path.append(root_path)

if sys.platform.startswith("linux"):
    python_lib_path = None
    if (platform.architecture()[0] == '32bit'):
        python_lib_path = os.path.abspath( os.path.join(root_path, "python27", "unix", "lib32"))
    else:
        python_lib_path = os.path.abspath( os.path.join(root_path, "python27", "unix", "lib64"))
    sys.path.append(python_lib_path)
elif sys.platform == "darwin":
    python_lib_path = os.path.abspath( os.path.join(root_path, "python27", "macos", "lib"))
    sys.path.append(python_lib_path)
    extra_lib = "/System/Library/Frameworks/Python.framework/Versions/2.7/Extras/lib/python/PyObjc"
    sys.path.append(extra_lib)
elif sys.platform == "win32":
    pass
else:
    raise RuntimeError("detect platform fail:%s" % sys.platform)

import string
import threading
import random
import hashlib
import ConfigParser

from ftplib import FTP, error_temp, error_perm
from socket import error as sock_error

from ossftp import ftpserver
from osssftp import sftpserver

import sys

is_py2 = (sys.version_info[0] == 2)
is_py3 = (sys.version_info[0] == 3)

if is_py2:
    bytes = str
    str = unicode
elif is_py3:
    bytes = bytes
    str = str

CONFIG_FILE = "test.cfg"

class myThread(threading.Thread):
    def __init__(self, thread_id, masquerade_address="", listen_address="127.0.0.1", port=2048,
                 log_level="DEBUG", bucket_endpoints="", internal=None, passive_ports='51000~52000', buff_size=1, protocol='https'):
        threading.Thread.__init__(self)
        self.thread_id = thread_id
        self.masquerade_address = masquerade_address
        self.listen_address = listen_address;
        self.port = port
        self.log_level = log_level
        self.bucket_endpoints = bucket_endpoints
        self.internal = internal
        self.passive_ports = passive_ports
        self.buff_size = buff_size
        self.protocol = protocol

    def run(self):
        print("ftp test starting ")
        ftpserver.start_ftp(self.masquerade_address, self.listen_address, self.port, self.log_level,
                            self.bucket_endpoints, self.internal, self.passive_ports, self.buff_size, self.protocol)
        print("ftp test ending")


class TestSftpThread(threading.Thread):
    def __init__(self, thread_id, listen_address="127.0.0.1", port=50000,
                 loglevel="DEBUG", bucket_endpoints="", internal=None, keyfile='test-rsa', buff_size=1, protocol='https'):
        threading.Thread.__init__(self)
        self.thread_id = thread_id
        self.listen_address = listen_address;
        self.port = port
        self.loglevel = loglevel
        self.bucket_endpoints = bucket_endpoints
        self.internal = internal
        self.keyfile = keyfile
        self.buff_size = buff_size
        self.protocol = protocol

    def run(self):
        print("sftp test starting ")
        sftpserver.start_sftp(self.listen_address, self.port, self.loglevel,
                              self.bucket_endpoints, self.internal, self.keyfile, self.buff_size, self.protocol)
        print("sftp test ending")


def get_value_from_config(section, option):
    value = ""
    if os.path.isfile(CONFIG_FILE):
        cf = ConfigParser.RawConfigParser()
        cf.read(CONFIG_FILE)
        if cf.has_section(section):
            value = cf.get(section, option)
    return value

def random_string(n):
    return ''.join(random.choice(string.ascii_lowercase) for i in range(n))

def gen_file(filename, file_size):
    '''
    it will generate a file with given filename and file_size
    '''
    if (os.path.isfile(filename)) and (file_size == os.path.getsize(filename)):
        return
    elif (file_size >= 0):
        f = open(filename, 'w')
        f.write(random_string(file_size))
        f.close()

def get_file_md5(file_path):
    md5 = hashlib.md5()

    f = open(file_path)
    for line in f:
        md5.update(line)
    f.close()
    return md5.hexdigest()

def safe_remove_file(file_name):
    if os.path.isfile(file_name):
        os.remove(file_name)

def storebinary(ftp, file_name, path):
    try:
        ftp.storbinary("STOR %s" % path, open(file_name, 'rb'))
    except (error_temp, error_perm, sock_error) as e:
        print(e)
        return False
    return True

def retrbinary(ftp, path, file_name):
    try:
        ftp.retrbinary("RETR %s" % path, open(file_name, 'wb').write)
    except (error_temp, error_perm, sock_error) as e:
        print(e)
        return False
    return True

def delete_file(ftp, path):
    try:
        ftp.delete(path)
    except (error_temp, error_perm, sock_error) as e:
        print(e)
        return False
    return True

def get_size(ftp, path):
    try:
        size = ftp.size(path)
    except (error_temp, error_perm, sock_error) as e:
        print(e)
        return -1
    return size
