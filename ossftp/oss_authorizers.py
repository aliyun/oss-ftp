# -*- coding: utf-8 -*-
import os, sys

import time
import logging

from pyftpdlib.authorizers import DummyAuthorizer
from pyftpdlib.authorizers import AuthenticationFailed
from pyftpdlib.authorizers import AuthorizerError
import oss2
from oss2.compat import str

import defaults
from launcher import config
from launcher.config import ACCESS_ID, ACCESS_SECRET, BUCKET_NAME, HOME_DIR

class BucketLoginInfo():
    def __init__(self, bucket_name, access_key_id, access_key_secret, endpoint):
        self.bucket_name = bucket_name
        self.endpoint = endpoint
        self.access_key = {access_key_id:access_key_secret}
        self.expire_time = time.time() + 60

    def update_access_key(self, access_key_id, access_key_secret):
        self.access_key[access_key_id] = access_key_secret
        self.expire_time = time.time() + 60

    def expired(self):
        return self.expire_time < time.time()

class UserInfo():
    def __init__(self, bucket_name, home_dir):
        self.bucket_name = bucket_name
        self.home_dir = home_dir

class OssAuthorizer(DummyAuthorizer):
    read_perms = u"elr"
    write_perms = u"adfmwM"
    default_endpoint = u"oss-cn-hangzhou.aliyuncs.com"
    LOCAL_CHECK_OK = 0
    LOCAL_CHECK_FAIL = 1
    LOCAL_CHECK_UNCERTAIN = 2
    
    def __init__(self):
        self.bucket_info_table = {}
        self.expire_time_interval = 60
        self.internal = None
        self.bucket_endpoints = {}
        self.user_info_table = {}

    def parse_username(self, username):
        if len(username) == 0:
            raise AuthorizerError("username can't be empty!")
        index = username.rfind('/')
        if index == -1:
            raise AuthorizerError("username %s is not in right format, it should be like ACCESS_ID/BUCKET_NAME" % username)
        elif index == len(username) - 1:
            raise AuthorizerError("bucketname can't be empty!")
        elif index == 0:
            raise AuthorizerError("ACCESS_ID can't be empty!")

        return  username[index+1:], username[:index]
    
    def log_bucket_info(self, bucket_name, endpoint, access_key_id):
        work_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
        file_name = work_dir + '/data/ossftp/ossftp.info'
        logger = logging.getLogger('pyftpdlib')
        try:
            f = open(file_name, 'a')
            time_str = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))
            record = "%s\tBucket:%s\tEndpoint:%s\tAccessID:%s\n" % (time_str, bucket_name, endpoint, access_key_id)
            f.write(record)
            f.close()
            logger.info("recording bucket access info succeed.%s" % record)
        except IOError as err:
            logger.error("error recording bucket access info.%s" % unicode(err))

    def put_bucket_info(self, bucket_name, endpoint, access_key_id, access_key_secret):
        if bucket_name not in self.bucket_info_table:
            self.bucket_info_table[bucket_name] = BucketLoginInfo(bucket_name, 
                    access_key_id, access_key_secret, endpoint)
        else:
            bucket_info = self.get_bucket_info(bucket_name)
            bucket_info.update_access_key(access_key_id, access_key_secret)
        self.log_bucket_info(bucket_name, endpoint, access_key_id)

    def get_bucket_info(self, bucket_name):
        return self.bucket_info_table.get(bucket_name)

    def delete_bucket_info(self, bucket_name):
        self.bucket_info_table.pop(bucket_name, None)

    def get_endpoint(self, bucket_name, location, access_key_id, access_key_secret):
        #try if can connect through internal domain
        internal_endpoint = location + "-internal" + ".aliyuncs.com"
        public_endpoint = location + ".aliyuncs.com"
        if self.internal is True:
            return internal_endpoint
        elif self.internal is False:
            return public_endpoint

        try:
            bucket = oss2.Bucket(oss2.Auth(access_key_id, access_key_secret), internal_endpoint, bucket_name, connect_timeout=1.0, app_name=defaults.app_name)
            res = bucket.get_bucket_acl()
        except oss2.exceptions.OssError as e:
            return public_endpoint
        return internal_endpoint

    def oss_check(self, bucket_name, default_endpoint, access_key_id, access_key_secret):
        # 1. when specify bucket endpoints
        if bucket_name in self.bucket_endpoints:
            endpoint = self.bucket_endpoints[bucket_name]
            try:
                bucket = oss2.Bucket(oss2.Auth(access_key_id, access_key_secret), endpoint, bucket_name, connect_timeout=5.0, app_name=defaults.app_name)
                faked_obj_name = "test-faked-objname-to-check-ak-if-right"
                res = bucket.get_object(faked_obj_name)
            except oss2.exceptions.NoSuchKey as e:
                pass
            except oss2.exceptions.AccessDenied as e:
                raise AuthenticationFailed("get random object was denied, check your access_key/access_id.request_id:%s, status:%s, code:%s, message:%s"% (e.request_id, unicode(e.status), e.code, e.message))
            except oss2.exceptions.OssError as e:
                raise AuthenticationFailed("access bucket:%s using specified \
                        endpoint:%s failed. request_id:%s, status:%s, code:%s, message:%s" % (bucket_name, endpoint, e.request_id, unicode(e.status), e.code, e.message))
            return endpoint 
        
        # 2. when not specify bucket endpoints
        try:
            service = oss2.Service(oss2.Auth(access_key_id, access_key_secret), default_endpoint, app_name=defaults.app_name)
            res = service.list_buckets(prefix=bucket_name)
        except oss2.exceptions.AccessDenied as e:
            raise AuthenticationFailed("can't list buckets, check your access_key.request_id:%s, status:%s, code:%s, message:%s"% (e.request_id, unicode(e.status), e.code, e.message))
        except oss2.exceptions.OssError as e:
            raise AuthenticationFailed("list buckets error. request_id:%s, status:%s, code:%s, message:%s" % (e.request_id, unicode(e.status), e.code, e.message))
        
        # 3. internal_endpoint or public_endpoint
        bucket_list = res.buckets
        for bucket in bucket_list:
            if bucket.name == bucket_name:
                endpoint = self.get_endpoint(bucket_name, str(bucket.location), access_key_id, access_key_secret)
                return endpoint
        raise AuthenticationFailed("can't find the bucket %s when list buckets." % bucket_name) 

    def local_check(self, bucket_name, access_key_id, access_key_secret):
        bucket_info = self.get_bucket_info(bucket_name)
        if bucket_info is None:
            return self.LOCAL_CHECK_UNCERTAIN 
        if bucket_info.expired():
            self.delete_bucket_info(bucket_name)
            return self.LOCAL_CHECK_UNCERTAIN
        if access_key_id not in bucket_info.access_key:
            return self.LOCAL_CHECK_UNCERTAIN
        if bucket_info.access_key[access_key_id] != access_key_secret:
            raise AuthenticationFailed("AuthFailed, bucket:%s, access_key_id:%s, access_key_secret is not right" % (bucket_name, access_key_id))
        else:
            return self.LOCAL_CHECK_OK

    def validate_authentication(self, username, password, handler):
        """Raises AuthenticationFailed if supplied username and
        password don't match the stored credentials, else return
        None.
        """
        account_info = config.get_account_info(username, password)
        bucket_name = None
        access_key_id = None
        access_key_secret = None
        if account_info is None:
            bucket_name, access_key_id = self.parse_username(username)
            access_key_secret = password
        else:
            access_key_id = account_info[ACCESS_ID]
            access_key_secret = account_info[ACCESS_SECRET]
            bucket_name = account_info[BUCKET_NAME]
            home_dir = account_info[HOME_DIR].strip('/')
            user_info = UserInfo(bucket_name, home_dir)
            self.user_info_table[username] = user_info
        res = self.local_check(bucket_name, access_key_id, access_key_secret)
        if res == self.LOCAL_CHECK_OK:
            return
        endpoint = self.oss_check(bucket_name, self.default_endpoint, access_key_id, access_key_secret)
        self.put_bucket_info(bucket_name, endpoint, access_key_id, access_key_secret)

    def get_home_dir(self, username):
        """Return the user's home directory.
        Since this is called during authentication (PASS),
        AuthenticationFailed can be freely raised by subclasses in case
        the provided username no longer exists.
        """
        user_info = self.user_info_table.get(username)
        if user_info:
            if user_info.home_dir:
                return '/' + user_info.bucket_name + '/' + user_info.home_dir + '/'
            else:
                return '/' + user_info.bucket_name + '/'
        else:
            bucket_name, access_key_id = self.parse_username(username)
            bucket_name = bucket_name.strip('/')
            return '/' + bucket_name + '/'

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
        msg = None
        if self.user_info_table.get(username):
            bucket_name = self.user_info_table.get(username).bucket_name
            msg = u"login to bucket: %s with login username: %s" % (bucket_name, username)
        else:
            bucket_name, access_key_id = self.parse_username(username)
            msg = u"login to bucket: %s with access_key_id: %s" % (bucket_name, access_key_id)
        return msg

    def get_msg_quit(self, username):
        """Return the user's quitting message."""
        msg = None
        if self.user_info_table.get(username):
            bucket_name = self.user_info_table.get(username).bucket_name
            msg = u"logout of bucket: %s with login username: %s" % (bucket_name, username)
        else:
            bucket_name, access_key_id = self.parse_username(username)
            msg = u"logout of bucket: %s with access_key_id: %s" % (bucket_name, access_key_id)
        return msg
