# -*- coding: utf-8 -*-
import os
from pyftpdlib.authorizers import DummyAuthorizer
from pyftpdlib.authorizers import AuthenticationFailed

# common dir is in root_path that has already added into sys.path
from common.oss_authorizer import OssAuthorizer


class FtpAuthorizer(DummyAuthorizer, OssAuthorizer):
    read_perms = u"elr"
    write_perms = u"adfmwM"

    def __init__(self):
        work_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
        log_file = work_dir + '/data/ossftp/ossftp.info'
        logger_name = 'pyftpdlib'
        OssAuthorizer.__init__(self, log_file, logger_name)

    def validate_authentication(self, username, password, handler):
        """Raises AuthenticationFailed if supplied username and
        password don't match the stored credentials, else return
        None.
        """
        try:
            bucket_name, access_key_id = self.parse_username(username)
            access_key_secret = password
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
        bucket_name, access_key_id = self.parse_username(username)
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
        bucket_name, access_key_id = self.parse_username(username)
        msg = u"login to bucket: %s with access_key_id: %s" % (bucket_name, access_key_id)
        return msg 

    def get_msg_quit(self, username):
        """Return the user's quitting message."""
        bucket_name, access_key_id = self.parse_username(username)
        msg = u"logout of bucket: %s with access_key_id: %s" % (bucket_name, access_key_id)
        return msg 
