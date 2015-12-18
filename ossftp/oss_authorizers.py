# -*- coding: utf-8 -*-
import os
import logging

from pyftpdlib.authorizers import DummyAuthorizer
from pyftpdlib.authorizers import AuthenticationFailed
from pyftpdlib.authorizers import AuthorizerError
import time

import oss2
import defaults
class OssAuthorizer(DummyAuthorizer):
    read_perms = u"elr"
    write_perms = u"adfmwM"
    default_location = u"oss-cn-hangzhou"
    default_endpoint = u"oss-cn-hangzhou.aliyuncs.com"
    internal = None
    
    def __init__(self):
        self.bucket_info_table = {}
        self.expire_time = 10
        self.error_bucket_expire_time = 5

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
    
    def log_bucket_info(self, bucket_name, endpoint, access_id):
        work_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
        file_name = work_dir + '/data/ossftp/ossftp.info'
        logger = logging.getLogger('pyftpdlib')
        try:
            f = open(file_name, 'a')
            time_str = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))
            record = "%s\tBucket:%s\tEndpoint:%s\tAccessID:%s\n" % (time_str, bucket_name, endpoint, access_id)
            f.write(record)
            f.close()
            logger.info("recording bucket access info succeed.%s" % record)
        except IOError as err:
            logger.error("error recording bucket access info.%s" % unicode(err))

    def put_bucket_info(self, bucket_name, endpoint, access_id, access_key):
        info_expire_time = time.time() + self.expire_time
        if bucket_name not in self.bucket_info_table:
            access_key_dict = {}
            access_key_dict[access_id] = access_key
            self.bucket_info_table[bucket_name] = {
                    u"endpoint": endpoint,
                    u"access_key_dict": access_key_dict,
                    u"info_expire_time": info_expire_time
            }
            self.log_bucket_info(bucket_name, endpoint, access_id)
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
        if bucket_name in self.bucket_info_table:
            del self.bucket_info_table[bucket_name]

    def get_endpoint(self, bucket_name, location, access_id, access_key):
        #try if can connect through internal domain
        internal_endpoint = location + "-internal" + ".aliyuncs.com"
        public_endpoint = location + ".aliyuncs.com"
        if self.internal is True:
            return internal_endpoint
        elif self.internal is False:
            return public_endpoint

        try:
            bucket = oss2.Bucket(oss2.Auth(access_id, access_key), internal_endpoint, bucket_name, connect_timeout=1.0, app_name=defaults.app_name)
            res = bucket.get_bucket_acl()
        except oss2.exceptions.OssError as e:
            return public_endpoint
        return internal_endpoint

    def _check_loggin(self, bucket_name, default_endpoint, access_id, access_key):
        try:
            service = oss2.Service(oss2.Auth(access_id, access_key), default_endpoint, app_name=defaults.app_name)
            res = service.list_buckets(prefix=bucket_name)
            bucket_list = res.buckets
            for bucket in bucket_list:
                if bucket.name == bucket_name:
                    endpoint = self.get_endpoint(bucket_name, bucket.location.decode('utf-8'), access_id, access_key)
                    return endpoint
            raise AuthenticationFailed("can't find the bucket %s when list buckets." % bucket_name) 
        except oss2.exceptions.OssError as e:
            raise AuthenticationFailed("get bucket %s endpoint error, request_id: %s, status: %s, code: %s" % (bucket_name, e.request_id, e.status, e.code))

    def validate_authentication(self, username, password, handler):
        """Raises AuthenticationFailed if supplied username and
        password don't match the stored credentials, else return
        None.
        """
        bucket_name, access_id = self.parse_username(username)
        access_key = password
        endpoint = self._check_loggin(bucket_name, self.default_endpoint, access_id, access_key)
        self.put_bucket_info(bucket_name, endpoint, access_id, access_key)

    def get_home_dir(self, username):
        """Return the user's home directory.
        Since this is called during authentication (PASS),
        AuthenticationFailed can be freely raised by subclasses in case
        the provided username no longer exists.
        """
        bucket_name, access_id = self.parse_username(username)
        bucket_name = bucket_name.strip('/')
        bucket_name = '/' + bucket_name + '/'
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
        bucket_name, access_id = self.parse_username(username)
        msg = u"login to bucket: %s with access_id: %s" % (bucket_name, access_id)
        return msg 

    def get_msg_quit(self, username):
        """Return the user's quitting message."""
        bucket_name, access_id = self.parse_username(username)
        msg = u"logout of bucket: %s with access_id: %s" % (bucket_name, access_id)
        return msg 
