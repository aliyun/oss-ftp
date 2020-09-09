import os
import string
import threading
import random
import hashlib
import ConfigParser

from ftplib import FTP, error_temp, error_perm
from socket import error as sock_error

from ossftp import ftpserver

CONFIG_FILE="test.cfg"

class myThread(threading.Thread):

    def __init__(self, thread_id, masquerade_address="", listen_address="127.0.0.1",port=2048, log_level="DEBUG", bucket_endpoints="", internal=None, passive_ports=None):
        threading.Thread.__init__(self)
        self.thread_id = thread_id
        self.masquerade_address = masquerade_address
        self.listen_address = listen_address;
        self.port = port
        self.log_level = log_level
        self.bucket_endpoints = bucket_endpoints
        self.internal = internal
        self.passive_ports = passive_ports

    def run(self):
        ftpserver.start_ftp(self.masquerade_address, self.listen_address, self.port, self.log_level, self.bucket_endpoints, self.internal, self.passive_ports)

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
        print e
        return False
    return True

def retrbinary(ftp, path, file_name):
    try:
        ftp.retrbinary("RETR %s" % path, open(file_name, 'wb').write)
    except (error_temp, error_perm, sock_error) as e:
        print e
        return False
    return True

def delete_file(ftp, path):
    try:
        ftp.delete(path)
    except (error_temp, error_perm, sock_error) as e:
        print e
        return False
    return True

def get_size(ftp, path):
    try:
        size = ftp.size(path)
    except (error_temp, error_perm, sock_error) as e:
        print e
        return -1
    return size 
