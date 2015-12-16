# -*- coding: utf-8 -*-

from pyftpdlib.filesystems import FilesystemError
import time
import datetime
import types

import oss2
from oss2.exceptions import *
from . import defaults

class TrickFile:
    def __init__(self, name, resp):
        self.name = name
        self.resp = resp
        self.closed = False

    def read(self, amt=None):
        return self.resp.read(amt)

    def close(self):
        pass

class OssFileOperation:
    
    def __init__(self, bucket, key, size_cache, dir_cache):
        self.bucket = bucket
        self.key = key.lstrip('/')
        self.size_cache = size_cache
        self.dir_cache = dir_cache
        self.expire_time = 10

        self.buf = ''
        self.buflimit = defaults.send_data_buff_size
        self.closed = False
        self.name = self.bucket.bucket_name + '/' + self.key
        self.upload_id = None
        self.part_num = None
        self.part_list = []
        self.max_retry_times = defaults.max_send_retry_times
        self.contents = None

    def get_upload_id(self):
        if self.upload_id is not None:
            return self.upload_id
        retry = self.max_retry_times
        status, code, request_id = "", "", ""
        while retry > 0:
            retry -= 1
            try:
                resp = self.bucket.init_multipart_upload(self.key)
                self.upload_id = resp.upload_id
                self.part_num = 0
                return self.upload_id
            except OssError as e:
                status, code, request_id = e.status, e.code, e.request_id
        raise FilesystemError("init_multi_upload failed. bucket:%s, key:%s, \
                    request_id:%s, code:%s, status:%s" % (self.bucket.bucket_name,
                    self.key, request_id, code, status))

    def send_buf(self):
        upload_id = self.get_upload_id()
        assert upload_id is not None
        if not self.buf:
            return
        self.part_num += 1
        retry = self.max_retry_times
        status, code, request_id = "", "", ""
        while retry > 0:
            retry -= 1
            try:
                res = self.bucket.upload_part(self.key, upload_id, self.part_num, self.buf)
                self.buf = ''
                self.part_list.append(oss2.models.PartInfo(self.part_num, res.etag))
                return
            except OssError as e:
                status, code, request_id = e.status, e.code, e.request_id
        raise FilesystemError("upload part failed. bucket:%s, key:%s, part_num:%s\
                    request_id:%s, code:%s, status:%s" % (self.bucket.bucket_name,
                    self.key, self.part_num, request_id, code, status))
        
    def write(self, data):
        while len(data) + len(self.buf) > self.buflimit:
            _len = self.buflimit - len(self.buf)
            self.buf = self.buf + data[:_len]
            data = data[_len:]
            self.send_buf()
        self.buf += data
        
    def close(self):
        assert self.closed == False
        if not self.upload_id:
            retry = self.max_retry_times
            status, code, request_id = "", "", ""
            while retry > 0:
                retry -= 1
                try:
                    self.bucket.put_object(self.key, self.buf)
                    return
                except OssError as e:
                    status, code, request_id = e.status, e.code, e.request_id
            
            raise FilesystemError("put key failed. bucket:%s, key:%s, \
                    request_id:%s, code:%s, status:%s" % (self.bucket.bucket_name,
                    self.key, request_id, code, status))
        
        self.send_buf()
        upload_id = self.get_upload_id()
        retry = self.max_retry_times
        complete_ok = False
        status, code, request_id = "", "", ""
        while retry > 0:
            retry -= 1
            try:
                self.bucket.complete_multipart_upload(self.key, upload_id, self.part_list)
                complete_ok = True
                break
            except OssError as e:
                status, code, request_id = e.status, e.code, e.request_id
        if not complete_ok:
            raise FilesystemError("complete_multipart_upload failed. bucket:%s, \
                    key:%s, upload_id:%s, request_id:%s, code:%s, status:%s" \
                    % (self.bucket.bucket_name, self.key, upload_id, request_id, code, status))
        self.closed = True
    
    def listdir(self):
        if self.contents:
            return self.contents
        key = self.key
        if key != '' and not key.endswith('/'):
            key = key + '/'
        self.key_list = []
        self.dir_list = []
        for i, key_info in enumerate(oss2.iterators.ObjectIterator(self.bucket, prefix=key, delimiter='/')):
            if key_info.is_prefix():
                self.dir_list.append(key_info.key)
            else:
                self.key_list.append(key_info)
        self.contents = []
        for entry in self.key_list:
            to_add = entry.key.decode('utf-8')[len(key):]
            last_modified = entry.last_modified
            last_modified_str = datetime.datetime.utcfromtimestamp(last_modified).strftime('%Y/%m/%d %H:%M:%S')
            self.contents.append((to_add, entry.size, last_modified_str.decode('utf-8')))
            self.cache_set(self.size_cache, (self.bucket.bucket_name, entry.key), entry.size)
        for entry in self.dir_list:
            to_add = entry.decode('utf-8')[len(key):]
            self.contents.append((to_add, -1, 0))
        return self.contents
        
    def isfile(self):
        value = self.cache_get(self.dir_cache, (self.bucket.bucket_name, self.key))
        if value is not None:
            return not value
        self.listdir()
        value = (len(self.contents) == 0)
        self.cache_set(self.dir_cache, (self.bucket.bucket_name, self.key), not value)
        return value

    def isdir(self):
        value = self.cache_get(self.dir_cache, (self.bucket.bucket_name, self.key))
        if value is not None:
            return value
        value = not self.isfile()
        self.cache_set(self.dir_cache, (self.bucket.bucket_name, self.key), value)
        return value
    
    def cache_get(self, cache, key):
        if cache.has_key(key) and cache[key][1] + self.expire_time >= time.time():
            return cache[key][0]
        else:
            return None
    
    def cache_set(self, cache, key, value):
        cache[key] = (value, time.time())
    
    def getsize(self):
        value = self.cache_get(self.size_cache, (self.bucket.bucket_name, self.key))
        if value != None:
            return value
        content_length = 0
        try:
            resp = self.bucket.head_object(self.key)
            content_length = resp.content_length
            self.cache_set(self.size_cache, (self.bucket.bucket_name, self.key), content_length)
        except OssError as e:
            raise FilesystemError("head object failed. bucket:%s, key:%s, \
                    request_id:%s, code:%s, status:%s" % (self.bucket.bucket_name,
                    self.key, e.request_id, e.code, e.status))
        return content_length 
    
    def open_read(self):
        retry = self.max_retry_times
        status, code, request_id = "", "", ""
        while retry > 0:
            retry -= 1
            try:
                resp = self.bucket.get_object(self.key)
                return TrickFile(self.name, resp) 
            except OssError as e:
                status, code, request_id = e.status, e.code, e.request_id
        raise FilesystemError("get object failed. bucket:%s, key:%s, \
                request_id:%s, code:%s, status:%s" % (self.bucket.bucket_name,
                self.key, request_id, code, status))
         
    def mkdir(self):
        key = self.key
        if not key.endswith('/'):
            key = key + '/'
        retry = self.max_retry_times
        status, code, request_id = "", "", ""
        while retry > 0:
            retry -= 1
            try:
                resp = self.bucket.put_object(key, "")
                self.cache_set(self.dir_cache, (self.bucket.bucket_name, self.key), True)
                return
            except OssError as e:
                status, code, request_id = e.status, e.code, e.request_id
        raise FilesystemError("mkdir failed. bucket:%s, key:%s, \
                request_id:%s, code:%s, status:%s" % (self.bucket.bucket_name,
                key, request_id, code, status))
            
    def rmdir(self):
        key = self.key
        if not key.endswith('/'):
            key = key + '/'
        retry = self.max_retry_times
        status, code, request_id = "", "", ""
        while retry > 0:
            retry -= 1
            try:
                self.bucket.delete_object(key)
                self.cache_set(self.dir_cache, (self.bucket.bucket_name, self.key), False)
                return
            except OssError as e:
                status, code, request_id = e.status, e.code, e.request_id
        raise FilesystemError("delete dir failed. bucket:%s, key:%s, \
                request_id:%s, code:%s, status:%s" % (self.bucket.bucket_name,
                key, request_id, code, status))

    def remove(self):
        key = self.key
        retry = self.max_retry_times
        status, code, request_id = -1, '', ''
        while retry > 0:
            retry -= 1
            try:
                self.bucket.delete_object(key)
                return
            except OssError as e:
                status, code, request_id = e.status, e.code, e.request_id
        raise FilesystemError("delete file failed. bucket:%s, key:%s, \
                request_id:%s, code:%s, status:%s" % (self.bucket.bucket_name,
                key, request_id, code, status))
