# -*- coding:utf-8 -*-
import os, sys

current_path = os.path.dirname(os.path.abspath(__file__))
root_path = os.path.abspath( os.path.join(current_path, os.pardir))
sys.path.append(root_path)

import threading
import time
import unittest
from socket import error as sock_error
from ftplib import FTP, FTP_TLS, error_temp, error_perm

from ossftp import ftpserver
from util import *

class LoginTest(unittest.TestCase):

    def setUp(self):
        self.host = get_value_from_config("ftpconfig", "host") 
        self.ftp_port = int(get_value_from_config("ftpconfig", "ftp_port"))
        self.username = get_value_from_config("ftpconfig", "normal_id") + '/' + get_value_from_config("ftpconfig", "normal_bucket") 
        self.password = get_value_from_config("ftpconfig", "normal_key") 

    def tearDown(self):
        pass

    def ftp_login(self, username, password):
        try:
            ftp = FTP()
            ftp.connect(self.host, self.ftp_port)
            ftp.login(username, password)
            ftp.quit()
        except (error_temp, error_perm, sock_error) as e:
            return False
        else:
            return True

    def test_normal(self):
        self.assertTrue(self.ftp_login(self.username, self.password))
        #below login will hit cache
        self.assertTrue(self.ftp_login(self.username, self.password))
        #test wrong  access_key_sercrete
        self.assertFalse(self.ftp_login(self.username, self.password+"qwerasdf"))
        self.assertTrue(self.ftp_login(self.username, self.password))

    def test_specified(self):
        normal_id = get_value_from_config("ftpconfig", "normal_id") 
        normal_key = get_value_from_config("ftpconfig", "normal_key")
        specified_bucket = get_value_from_config("ftpconfig", "specified_bucket")
        username_specified = normal_id + "/" + specified_bucket
        self.assertTrue(self.ftp_login(username_specified, normal_key))
        
        wrong_user = "qwerasdf/%s" % specified_bucket
        wrong_pwd = "adfasdfqer"
        self.assertFalse(self.ftp_login(wrong_user, wrong_pwd))

    def test_child_account(self):
        normal_bucket = get_value_from_config("ftpconfig", "normal_bucket")
        specified_bucket = get_value_from_config("ftpconfig", "specified_bucket")
        child_id =  get_value_from_config("ftpconfig", "child_id")
        child_key = get_value_from_config("ftpconfig", "child_key")
        self.assertFalse(self.ftp_login(child_id+"/"+normal_bucket, child_key))
        self.assertTrue(self.ftp_login(child_id+"/"+specified_bucket, child_key))

    def test_update_ak(self):
        #first login with normal ak
        self.assertTrue(self.ftp_login(self.username, self.password))
        #then login with new ak
        username_new = get_value_from_config("ftpconfig", "normal_id_new") + '/' + get_value_from_config("ftpconfig", "normal_bucket") 
        password_new = get_value_from_config("ftpconfig", "normal_key_new") 
        self.assertTrue(self.ftp_login(username_new, password_new))

    def test_error_input(self):
        user_info = { "":"",
                "qqqqqq":"",
                "":"aaaaaaaa",
                "asdfasdf":"asdfsdf",
                "asdfasdf/":"aaaaaaaa",
                "/qwerdf":"aaaaaaaa"
                }
        for username, password in user_info.items():
            self.assertFalse(self.ftp_login(username, password))

    def test_no_such_bucket(self):
        user_info = { "adsfasdf/test-bucket-name-unittest":"randomaccesskey"
                }
        for username, password in user_info.items():
            self.assertFalse(self.ftp_login(username, password))

    def test_wrong_ak(self):
        normal_bucket = get_value_from_config("ftpconfig", "normal_bucket")
        user_info = { "adsfasdf/%s"%normal_bucket:"randomaccesskey"
                }
        for username, password in user_info.items():
            self.assertFalse(self.ftp_login(username, password))

if __name__ == '__main__':
    specified_url = get_value_from_config("ftpconfig", "specified_url")
    t = myThread("thread_id_1", "", "127.0.0.1", 2048, "DEBUG", specified_url)
    t.daemon = True
    t.start()
    #wait for ossftp ready
    time.sleep(5)
    unittest.main()
