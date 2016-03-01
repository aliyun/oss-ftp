# -*- coding: utf-8 -*-
import time
import datetime
import types

from pyftpdlib.filesystems import FilesystemError
import oss2
from oss2.exceptions import *

import defaults

class TrickFile:
    def __init__(self, name, resp):
        self.name = name
        self.resp = resp
        self.closed = False

    def read(self, amt=None):
        return self.resp.read(amt)

    def close(self):
        pass

def retry(fn):
    def wrapper(*args, **kwargs):
        oss_file_op_intance = args[0]
        retry = defaults.max_send_retry_times
        status, code, message, request_id = None, "", "", ""
        while retry > 0:
            retry -= 1
            try:
                return fn(*args, **kwargs)
            except OssError as e:
                status, code, message, request_id = e.status, e.code, e.message, e.request_id
        raise FilesystemError("%s failed. bucket:%s, key:%s,\
            request_id:%s, code:%s, status:%s, message:%s" % (fn.__name__,
            oss_file_op_intance.bucket.bucket_name, oss_file_op_intance.key,
            request_id, code, status, message))
    return wrapper

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
        self.contents = None

    @retry
    def init_multi_upload(self):
        resp = self.bucket.init_multipart_upload(self.key)
        self.upload_id = resp.upload_id
        self.part_num = 0
        self.part_list = []
        return self.upload_id

    def get_upload_id(self):
        if self.upload_id is not None:
            return self.upload_id
        else:
            return self.init_multi_upload()
    
    @retry
    def upload_part(self):
        return self.bucket.upload_part(self.key, self.upload_id, self.part_num, self.buf)

    def send_buf(self):
        upload_id = self.get_upload_id()
        assert upload_id is not None
        if not self.buf:
            return
        self.part_num += 1
        res = self.upload_part()
        self.buf = ''
        self.part_list.append(oss2.models.PartInfo(self.part_num, res.etag))
       
    def write(self, data):
        while len(data) + len(self.buf) > self.buflimit:
            _len = self.buflimit - len(self.buf)
            self.buf = self.buf + data[:_len]
            data = data[_len:]
            self.send_buf()
        self.buf += data
    
    @retry  
    def put_object(self, buf):
        self.bucket.put_object(self.key, buf)

    @retry
    def complete_multipart_upload(self):
        self.bucket.complete_multipart_upload(self.key, self.upload_id, self.part_list)

    def close(self):
        assert self.closed == False
        if self.upload_id is None:
            self.put_object(self.buf)
        else:
            self.send_buf()
            self.complete_multipart_upload()
        self.closed = True
    
    def listdir(self):
        key = self.key
        if key != '':
            key = key.rstrip('/') + '/'
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

    @retry
    def object_exists(self):
        return self.bucket.object_exists(self.key)

    def isfile(self):
        return self.object_exists()

    def isdir(self):
        value = self.cache_get(self.dir_cache, (self.bucket.bucket_name, self.key))
        if value is not None:
            return value
        contents = self.listdir()
        _is_dir = not  (len(contents) == 0)
        self.cache_set(self.dir_cache, (self.bucket.bucket_name, self.key), _is_dir)
        return _is_dir
    
    def cache_get(self, cache, key):
        if not cache.has_key(key):
            return None
        if cache[key][1] + self.expire_time >= time.time():
            return cache[key][0]
        else:
            self.cache_delete(cache, key)
            return None
    
    def cache_set(self, cache, key, value):
        cache[key] = (value, time.time())

    def cache_delete(self, cache, key):
        cache.pop(key, None)

    @retry
    def head_object(self):
        resp = self.bucket.head_object(self.key)
        content_length = resp.content_length
        return content_length
   
    @retry
    def getmtime(self):
        resp = self.bucket.head_object(self.key)
        mtime = resp.last_modified
        return mtime

    def getsize(self):
        value = self.cache_get(self.size_cache, (self.bucket.bucket_name, self.key))
        if value != None:
            return value
        content_length = self.head_object()
        self.cache_set(self.size_cache, (self.bucket.bucket_name, self.key), content_length)
        return content_length
 
    @retry
    def get_object(self):
        resp = self.bucket.get_object(self.key)
        return TrickFile(self.name, resp)

    def open_read(self):
        return self.get_object()
       
    def mkdir(self):
        self.key = self.key.rstrip('/') + '/'
        self.put_object('')
        self.key = self.key.rstrip('/')
        self.cache_set(self.dir_cache, (self.bucket.bucket_name, self.key), True)

    @retry
    def delete_object(self):
        self.bucket.delete_object(self.key)

    def rmdir(self):
        self.key = self.key.rstrip('/') + '/'
        self.delete_object()
        self.key = self.key.rstrip('/')
        self.cache_set(self.dir_cache, (self.bucket.bucket_name, self.key), False)

    def remove(self):
        self.delete_object()
        self.cache_delete(self.size_cache, (self.bucket.bucket_name, self.key))
