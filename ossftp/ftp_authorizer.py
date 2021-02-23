# -*- coding: utf-8 -*-
import os
from pyftpdlib.authorizers import DummyAuthorizer
from pyftpdlib.authorizers import AuthenticationFailed

# The common dir in root path has been added into sys.path
from common.oss_authorizer import OssAuthorizer
from launcher import config
from launcher.config import ACCESS_ID, ACCESS_SECRET, BUCKET_NAME, HOME_DIR


class UserInfo():
    def __init__(self, bucket_name, home_dir):
        self.bucket_name = bucket_name
        self.home_dir = home_dir


class FtpAuthorizer(DummyAuthorizer, OssAuthorizer):
    read_perms = u"elr"
    write_perms = u"adfmwM"

    def __init__(self):
        work_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
        log_file = work_dir + '/data/ossftp/ossftp.info'
        logger_name = 'pyftpdlib'
        OssAuthorizer.__init__(self, log_file, logger_name)
        self.user_info_table = {}

    def validate_authentication(self, username, password, handler):
        """Raises AuthenticationFailed if supplied username and
        password don't match the stored credentials, else return
        None.
        """
        try:
            # bucket_name, access_key_id = self.parse_username(username)
            # access_key_secret = password
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
        except Exception as e:
            raise AuthenticationFailed(e)

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
