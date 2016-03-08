# -*- coding: utf-8 -*-
import os, sys

current_path = os.path.dirname(os.path.abspath(__file__))
root_path = os.path.abspath( os.path.join(current_path, os.pardir))
sys.path.append(root_path)

import threading
import time
import uuid
import unittest
from socket import error as sock_error

from ftplib import FTP, FTP_TLS, error_temp, error_perm
from ossftp import ftpserver

from util import *

class FileTest(unittest.TestCase):

    def setUp(self):
        self.host = get_value_from_config("ftpconfig", "host") 
        self.ftp_port = int(get_value_from_config("ftpconfig", "ftp_port"))
        self.username = get_value_from_config("ftpconfig", "normal_id") + '/' + get_value_from_config("ftpconfig", "normal_bucket") 
        self.password = get_value_from_config("ftpconfig", "normal_key") 
        self.ftp = FTP()
        self.ftp.connect(self.host, self.ftp_port)
        self.ftp.login(self.username, self.password)

    def tearDown(self):
        self.ftp.quit()

    def test_upload(self):
        #size_list = [1024, 4*1024, 16*1024, 1024*1024, 16*1024*1024, 1024*1024*1024]
        size_list = [1024, 4*1024, 16*1024, 1024*1024, 16*1024*1024]
        up_file = "up_file"
        down_file = "down_file"
        for size in size_list:
            gen_file(up_file, size)
            _md5_up = get_file_md5(up_file)
            path = unicode(time.time())
            self.assertTrue(storebinary(self.ftp, up_file, path))

            self.assertTrue(retrbinary(self.ftp, path, down_file))
            _md5_down = get_file_md5(down_file) 
            self.assertEqual(_md5_up, _md5_down)
            self.assertTrue(delete_file(self.ftp, path))
        
        safe_remove_file(up_file)
        safe_remove_file(down_file)

    def test_get_size(self):
        up_file = "up_file"
        size = 1024
        gen_file(up_file, size)
        path = unicode(time.time())
        self.assertTrue(storebinary(self.ftp, up_file, path))
        curr_size = get_size(self.ftp, path) 
        self.assertEqual(size, curr_size)
        self.assertTrue(delete_file(self.ftp, path))

        safe_remove_file(up_file)

    def test_rename(self):
        up_file = "up_file"
        size = 1024
        gen_file(up_file, size)
        path = unicode(time.time())
        self.assertTrue(storebinary(self.ftp, up_file, path))

        try:
            self.ftp.rename(path, path+"_dst_name")
        except error_perm as e:
            self.assertEqual(e[0], "550 method rename not implied.")
        else:
            self.fail("test_rename failed")
        self.assertTrue(delete_file(self.ftp, path))
       
        safe_remove_file(up_file)

    def test_chmod(self):
        up_file = "up_file"
        size = 1024
        gen_file(up_file, size)
        path = unicode(time.time())
        self.assertTrue(storebinary(self.ftp, up_file, path))

        try:
            self.ftp.sendcmd('SITE CHMOD 666 %s' % path)
        except error_perm as e:
            self.assertTrue(e[0], "550 method chmod is not implied.")
        else:
            self.fail("test_chmod failed")
        self.assertTrue(delete_file(self.ftp, path))

    def test_get_mtime(self):
        up_file = "up_file"
        size = 1024
        gen_file(up_file, size)
        path = unicode(time.time())
        self.assertTrue(storebinary(self.ftp, up_file, path))
        try:
            self.ftp.sendcmd('MDTM %s' % path)
        except (error_temp, error_perm, sock_error) as e:
            print e
            self.fail("test_get_mtime failed")
        self.assertTrue(delete_file(self.ftp, path))

    def test_file_name(self):
        file_name_list = ['中文', 'prefix_*&^% $#@!)(:?>', '中文1234&＊…………％＊&……＊&&％&……％&％＊&（！']
        up_file = "up_file"
        gen_file(up_file, 4*1024)
        _md5_up = get_file_md5(up_file)
        down_file = "down_file"
        for name in file_name_list:
            self.assertTrue(storebinary(self.ftp, up_file, name))
            self.assertTrue(retrbinary(self.ftp, name, down_file))
            _md5_down = get_file_md5(down_file) 
            self.assertEqual(_md5_up, _md5_down)
            self.assertTrue(delete_file(self.ftp, name))

        safe_remove_file(up_file)
        safe_remove_file(down_file)

    def test_list_file(self):
        up_file = "up_file"
        size = 1024
        gen_file(up_file, size)
        path = unicode(time.time())
        self.assertTrue(storebinary(self.ftp, up_file, path))
        data = []
        try:
            self.ftp.sendcmd('LIST %s' % path, )
        except (error_temp, error_perm, sock_error) as e:
            print e
            self.fail("test_list_file failed")
        self.assertTrue(delete_file(self.ftp, path))
 
if __name__ == '__main__':
    t = myThread("thread_id_1")
    t.daemon = True
    t.start()
    time.sleep(5)
    unittest.main()
