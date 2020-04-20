# -*- coding: utf-8 -*-

import logging
import time
import oss2
from oss2.compat import str


class BucketLoginInfo:
    def __init__(self, bucket_name, access_key_id, access_key_secret, endpoint):
        self.bucket_name = bucket_name
        self.endpoint = endpoint
        self.access_key = {access_key_id: access_key_secret}
        self.expire_time = time.time() + 60

    def update_access_key(self, access_key_id, access_key_secret):
        self.access_key[access_key_id] = access_key_secret
        self.expire_time = time.time() + 60

    def expired(self):
        return self.expire_time < time.time()


class OssAuthorizer(object):
    default_endpoint = u"oss-cn-hangzhou.aliyuncs.com"
    LOCAL_CHECK_OK = 0
    LOCAL_CHECK_FAIL = 1
    LOCAL_CHECK_UNCERTAIN = 2

    def __init__(self, log_file, logger_name):
        self.log_file = log_file
        self.logger_name = logger_name
        self.bucket_info_table = {}
        self.expire_time_interval = 60
        self.internal = None
        self.bucket_endpoints = {}

    def parse_username(self, username):
        if len(username) == 0:
            raise Exception("username can't be empty!")
        index = username.rfind('/')
        if index == -1:
            raise Exception(
                "username %s is not in right format, it should be like ACCESS_ID/BUCKET_NAME" % username)
        elif index == len(username) - 1:
            raise Exception("bucketname can't be empty!")
        elif index == 0:
            raise Exception("ACCESS_ID can't be empty!")

        return username[index + 1:], username[:index]

    def log_bucket_info(self, bucket_name, endpoint, access_key_id):
        logger = logging.getLogger(self.logger_name)
        try:
            f = open(self.log_file, 'a')
            time_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
            record = "%s\tBucket:%s\tEndpoint:%s\tAccessID:%s\n" % (time_str, bucket_name, endpoint, access_key_id)
            f.write(record)
            f.close()
            logger.info("recording bucket access info succeed.%s" % record)
        except IOError as err:
            logger.error("error recording bucket access info.%s" % str(err))

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
        # try if can connect through internal domain
        internal_endpoint = location + "-internal" + ".aliyuncs.com"
        public_endpoint = location + ".aliyuncs.com"
        if self.internal is True:
            return internal_endpoint
        elif self.internal is False:
            return public_endpoint

        try:
            bucket = oss2.Bucket(oss2.Auth(access_key_id, access_key_secret), internal_endpoint, bucket_name,
                                 connect_timeout=1.0)
            res = bucket.get_bucket_acl()
        except oss2.exceptions.OssError as e:
            return public_endpoint
        return internal_endpoint

    def oss_check(self, bucket_name, default_endpoint, access_key_id, access_key_secret):
        if bucket_name in self.bucket_endpoints:
            endpoint = self.bucket_endpoints[bucket_name]
            try:
                bucket = oss2.Bucket(oss2.Auth(access_key_id, access_key_secret), endpoint, bucket_name,
                                     connect_timeout=5.0)
                res = bucket.get_bucket_acl()
            except oss2.exceptions.OssError as e:
                raise Exception("access bucket:%s using specified \
                        endpoint:%s failed. request_id:%s, status:%s, code:%s, message:%s" % (
                bucket_name, endpoint, e.request_id, str(e.status), e.code, e.message))
            return endpoint
        try:
            service = oss2.Service(oss2.Auth(access_key_id, access_key_secret), default_endpoint)
            res = service.list_buckets(prefix=bucket_name)
        except oss2.exceptions.AccessDenied as e:
            raise Exception(
                "can't list buckets, check your access_key.request_id:%s, status:%s, code:%s, message:%s" % (
                e.request_id, str(e.status), e.code, e.message))
        except oss2.exceptions.OssError as e:
            raise Exception("list buckets error. request_id:%s, status:%s, code:%s, message:%s" % (
            e.request_id, str(e.status), e.code, e.message))

        bucket_list = res.buckets
        for bucket in bucket_list:
            if bucket.name == bucket_name:
                endpoint = self.get_endpoint(bucket_name, str(bucket.location), access_key_id,
                                             access_key_secret)
                return endpoint
        raise Exception("can't find the bucket %s when list buckets." % bucket_name)

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
            raise Exception("AuthFailed, bucket:%s, access_key_id:%s, access_key_secret is not right" % (
            bucket_name, access_key_id))
        else:
            return self.LOCAL_CHECK_OK
