# -*- coding: utf-8 -*-

import os
import oss2
import paramiko

# The common dir in root path has been added into sys.path
from common.oss_authorizer import OssAuthorizer
from common.util import wrap_protocol

from launcher import config
from launcher.config import ACCESS_ID, ACCESS_SECRET, BUCKET_NAME, HOME_DIR


class OssSftpAuthServer(paramiko.ServerInterface, OssAuthorizer):
    def __init__(self):
        self.protocol = 'https'
        work_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
        log_file = work_dir + '/data/osssftp/osssftp.info'
        logger_name = 'oss_sftp_auth'
        OssAuthorizer.__init__(self, log_file, logger_name)
        self.bucket = None
        self.home_dir = None

    def check_auth_password(self, username, password):
        account_info = config.get_account_info(username, password)
        bucket_name = None
        access_key_id = None
        access_key_secret = None
        self.home_dir = ''
        if account_info is None:
            bucket_name, access_key_id = self.parse_username(username)
            access_key_secret = password
        else:
            access_key_id = account_info[ACCESS_ID]
            access_key_secret = account_info[ACCESS_SECRET]
            bucket_name = account_info[BUCKET_NAME]
            self.home_dir = account_info[HOME_DIR].strip('/')

        res = self.local_check(bucket_name, access_key_id, access_key_secret)
        if res == self.LOCAL_CHECK_OK:
            endpoint = self.get_bucket_info(bucket_name).endpoint
            endpoint = wrap_protocol(endpoint, self.protocol)
            self.bucket = oss2.Bucket(oss2.Auth(access_key_id, access_key_secret), endpoint, bucket_name)
            return paramiko.AUTH_SUCCESSFUL

        endpoint = self.oss_check(bucket_name, self.default_endpoint, access_key_id, access_key_secret)
        self.put_bucket_info(bucket_name, endpoint, access_key_id, access_key_secret)
        endpoint = wrap_protocol(endpoint, self.protocol)
        self.bucket = oss2.Bucket(oss2.Auth(access_key_id, access_key_secret), endpoint, bucket_name)

        return paramiko.AUTH_SUCCESSFUL

    def check_auth_publickey(self, username, key):
        return paramiko.AUTH_FAILED

    def check_channel_request(self, kind, chanid):
        return paramiko.OPEN_SUCCEEDED