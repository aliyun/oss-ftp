# -*- coding:utf-8 -*-
import os, sys

current_path = os.path.dirname(os.path.abspath(__file__))
root_path = os.path.abspath( os.path.join(current_path, os.pardir))
sys.path.append(root_path)

import threading
import unittest
import time
from socket import error as sock_error

from ftplib import FTP, FTP_TLS,error_temp, error_perm
from ossftp import ftpserver

from util import *

class DirTest(unittest.TestCase):

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

    def test_mk_dir(self):
        dir_name_list = [unicode(time.time()), '中文目录', '中文目录测试!@@#)(*&^%$__＊（＊&……&＊', '__测试 这是目录 !qwer1234', '测试目录1层\测试目录2层']
        for dir_name in dir_name_list:
            try:
                self.ftp.mkd(dir_name)
                self.ftp.cwd(dir_name)
                self.ftp.cwd("..")
                self.ftp.rmd(dir_name)
            except (error_temp, error_perm, sock_error):
                self.fail("create dir error")

    def test_cwd_dir(self):
        try:
            dir_name = self.ftp.pwd() 
            data = []
            self.ftp.dir(data.append)
            for line in data:
                if line.startswith('drw'):
                    dir_name = line.split(' ')[-1]
                    break
            self.ftp.cwd(dir_name)
            data = []
            self.ftp.dir(data.append)
            self.ftp.cwd("..")
        except (error_temp, error_perm, sock_error):
            self.fail("cwd dir error")

    def test_chidr_empty(self):
        try:
            self.ftp.cwd("")
        except (error_temp, error_perm, sock_error):
            self.fail("cwd dir error")

    def test_list_dir(self):
        test_dir_name = unicode(time.time())
        try:
            self.ftp.mkd(test_dir_name)
            self.ftp.cwd(test_dir_name)
            file_1 = "file_1" + unicode(time.time())
            gen_file(file_1, 1024)
            self.ftp.storbinary("STOR %s" % file_1, open(file_1))
            file_2 = "file_2" + unicode(time.time())
            gen_file(file_2, 1024)
            self.ftp.storbinary("STOR %s" % file_2, open(file_2))
            tmp_dir = "tmp_dir" + unicode(time.time())
            self.ftp.mkd(tmp_dir)
            data = []
            self.ftp.dir(data.append)
            self.assertEqual(len(data), 3)
            data = []
            self.ftp.retrlines('MLSD', data.append)
            self.assertEqual(len(data), 3)
            self.ftp.cwd(tmp_dir)
            data = []
            self.ftp.retrlines('MLSD', data.append)
            self.assertEqual(len(data), 0)

            #clean
            self.ftp.rmd(tmp_dir)
            self.ftp.delete(file_1)
            self.ftp.delete(file_2)
            self.ftp.cwd("..")
            self.ftp.rmd(test_dir_name)
        except (error_temp, error_perm, sock_error):
            self.fail("list dir error")
        
        safe_remove_file(file_1)
        safe_remove_file(file_2)

    def test_list_root_dir(self):
        try:
            self.ftp.cwd('/')
            data = []
            self.ftp.retrlines('MLSD /', data.append)
        except (error_temp, error_perm, sock_error):
            self.fail("list dir error")

    def test_rm_dir(self):
        test_dir_name = unicode(time.time())
        try:
            self.ftp.mkd(test_dir_name)
            self.ftp.cwd(test_dir_name)
            self.ftp.cwd("..")
            self.ftp.rmd(test_dir_name)
        except (error_temp, error_perm, sock_error):
            self.fail("rm dir error")
        
        try:
            self.ftp.cwd(test_dir_name)
            self.fail("rmd dir error")
        except (error_temp, error_perm, sock_error):
            pass

    def test_rename_dir(self):
        test_dir_name = unicode(time.time())
        test_dir_name_to = test_dir_name + "_to"
        try:
            self.ftp.mkd(test_dir_name)
            self.ftp.rename(test_dir_name, test_dir_name_to)
            self.ftp.rmd(test_dir_name)
        except error_perm as e:
            self.assertEqual(e[0], "550 method rename not implied.")
        else:
            self.fail("check rename failed")

if __name__ == '__main__':
    t = myThread("thread_id_1")
    t.daemon = True
    t.start()
    time.sleep(5)
    unittest.main()
