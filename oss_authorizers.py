#!/usr/bin/env python
# $Id: authorizers.py 1171 2013-02-19 10:13:09Z g.rodola $

#  ======================================================================
#  Copyright (C) 2007-2013 Giampaolo Rodola' <g.rodola@gmail.com>
#
#                         All Rights Reserved
#
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation
# files (the "Software"), to deal in the Software without
# restriction, including without limitation the rights to use,
# copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following
# conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
# OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.
#
#  ======================================================================
from pyftpdlib.authorizers import DummyAuthorizer
from pyftpdlib.authorizers import AuthenticationFailed
from pyftpdlib.authorizers import AuthorizerError
from pyftpdlib._compat import PY3, unicode, getcwdu

import xml.etree.ElementTree as ET
import json
import os
import warnings
import errno
import sys
import time
import oss2

class OssAuthorizer(DummyAuthorizer):
    read_perms = "elr"
    write_perms = "adfmwM"
    endpoint = "oss-cn-hangzhou.aliyuncs.com"
    
    def __init__(self):
        self.bucket_info_table = {}
        self.expire_time = 60
        self.error_bucket_expire_time = 10

    def print_red(self, content):
        atrr = 1
        fore = 31
        color = "\x1B[%d;%dm" % (atrr,fore)
        print "%s%s\x1B[0m" % (color, content)

    def print_green(self, content):
        atrr = 1
        fore = 32
        color = "\x1B[%d;%dm" % (atrr,fore)
        print "%s%s\x1B[0m" % (color, content)

    def check_res(self, res, msg):
        if res.status / 100 != 2:
            self.print_red ('Error: %s error. ret:%s, req-id:%s, reason is:' % (msg, res.status, res.getheader("x-oss-request-id")))
            print res.read()
            raise ValueError('%s error' % msg)
        else:
            self.print_green ("%s success !" % msg)

    def parse_bucket_name(self, username):
        if username == "":
            raise ValueError("username can't be empty!")
        index = username.rfind('/')
        if index == -1:
            raise ValueError("username is not in right format.")
        return username[index+1:] 

    def parse_access_id(self, username):
        if username == "":
            raise ValueError("username can't be empty!")
        index = username.rfind('/')
        if index == -1:
            raise ValueError("username is not in right format.")
        return username[:index] 

    def put_bucket_info(self, bucket_name, endpoint, access_id, access_key):
        info_expire_time = time.time() + self.expire_time
        if bucket_name not in self.bucket_info_table:
            access_key_dict = {}
            access_key_dict[access_id] = access_key
            self.bucket_info_table[bucket_name] = {
                    "endpoint": endpoint,
                    "access_key_dict": access_key_dict,
                    "info_expire_time": info_expire_time
                    }
        else:
            #may need to update info
            if access_id not in self.bucket_info_table[bucket_name]["access_key_dict"]:
                self.bucket_info_table[bucket_name]["access_key_dict"][access_id] = access_key
                self.bucket_info_table[bucket_name]["info_expire_time"] = info_expire_time 

    def get_bucket_info(self, bucket_name):
        if bucket_name in self.bucket_info_table:
            return self.bucket_info_table[bucket_name]
        else:
            return None

    def delete_bucket_info(self, bucket_name):
        """Remove a user from the virtual users table."""
        if bucket_name in self.bucket_info_table:
            del self.bucket_info_table[bucket_name]

    def _check_loggin(self, bucket_name, endpoint, access_id, access_key):
        bucket = oss2.Bucket(oss2.Auth(access_id, access_key), endpoint, bucket_name)
        res = bucket.get_bucket_location()
        if res.status / 100 != 2:
            raise ValueError('access_id %s, access_key %s not match for bucket %s' % (access_id, access_key, bucket_name))
        self.put_bucket_info(bucket_name, endpoint, access_id, access_key)

    def validate_authentication(self, username, password, handler):
        """Raises AuthenticationFailed if supplied username and
        password don't match the stored credentials, else return
        None.
        """
        bucket_name = self.parse_bucket_name(username)
        endpoint = self.endpoint
        access_id = self.parse_access_id(username)
        access_key = password
        self._check_loggin(bucket_name, endpoint, access_id, access_key)

    def get_home_dir(self, username):
        """Return the user's home directory.
        Since this is called during authentication (PASS),
        AuthenticationFailed can be freely raised by subclasses in case
        the provided username no longer exists.
        """
        bucket_name = self.parse_bucket_name(username)
        if not bucket_name.startswith('/'):
            bucket_name = '/' + bucket_name
        if not bucket_name.endswith('/'):
            bucket_name = bucket_name + '/'
        return bucket_name 

    def impersonate_user(self, username, password):
        """Impersonate another user (noop).

        It is always called before accessing the filesystem.
        By default it does nothing.  The subclass overriding this
        method is expected to provide a mechanism to change the
        current user.
        """

    def terminate_impersonation(self, username):
        """Terminate impersonation (noop).

        It is always called after having accessed the filesystem.
        By default it does nothing.  The subclass overriding this
        method is expected to provide a mechanism to switch back
        to the original user.
        """

    def has_perm(self, username, perm, path=None):
        """Whether the user has permission over path (an absolute
        pathname of a file or a directory).

        Expected perm argument is one of the following letters:
        "elradfmwM".
        """
        return perm in (self.write_perms + self.read_perms)

    def get_perms(self, username):
        """Return current user permissions."""
        return self.write_perms + self.read_perms

    def get_msg_login(self, username):
        """Return the user's login message."""
        bucket_name = self.parse_bucket_name(username)
        access_id = self.parse_access_id(username)
        msg = "login to bucket: %s with access_id: %s" % (bucket_name, access_id)
        return msg 

    def get_msg_quit(self, username):
        """Return the user's quitting message."""
        bucket_name = self.parse_bucket_name(username)
        access_id = self.parse_access_id(username)
        msg = "logout of bucket: %s with access_id: %s" % (bucket_name, access_id)
        return msg 
