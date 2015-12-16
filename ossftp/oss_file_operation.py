# -*- coding: utf-8 -*-
from pyftpdlib._compat import PY3, u, unicode
from pyftpdlib.filesystems import FilesystemError
import time
import datetime
import pdb
import os
import types

import oss2
from oss2.exceptions import *
from . import defaults

class OssFileOperation:
    size_cache = {}
    dir_cache = {}
    expire_time = 10
    
    def __init__(self, bucket, object):
        self.bucket = bucket 
        self.object = self.stripFirstDelimiter(object)
        self.buf = ''
        self.buflimit = defaults.send_data_buff_size
        self.closed = False
        self.name = self.bucket.bucket_name + '/' + self.object
        self.upload_id = None
        self.max_retry_times = defaults.max_send_retry_times
        self.contents = None

    def stripFirstDelimiter(self, path):
        while path.startswith('/'):
            path = path[1:]
        return path
    
    def get_upload_id(self):
        if self.upload_id:
            return self.upload_id
        retry = self.max_retry_times
        status, code, request_id = "", "", ""
        while retry > 0:
            retry -= 1
            try:
                resp = self.bucket.init_multipart_upload(self.object)
                self.upload_id = resp.upload_id
                self.partNum = 0
                return self.upload_id
            except OssError as e:
                status, code, request_id = e.status, e.code, e.request_id
        raise FilesystemError("init_multi_upload failed. bucket:%s, object:%s, \
                    request_id:%s, code:%s, status:%s" % (self.bucket.bucket_name, \
                    self.object, request_id, code, status))

    def send_buf(self):
        upload_id = self.get_upload_id()
        assert upload_id != None
        if self.buf == '':
            return
        self.partNum += 1
        retry = self.max_retry_times
        status, code, request_id = "", "", ""
        while retry > 0:
            retry -= 1
            try:
                resp = self.bucket.upload_part(self.object, upload_id, self.partNum, self.buf)
                self.buf = ''
                return
            except OssError as e:
                status, code, request_id = e.status, e.code, e.request_id
        raise FilesystemError("upload part failed. bucket:%s, object:%s, partNum:%s\
                    request_id:%s, code:%s, status:%s" % (self.bucket.bucket_name, \
                    self.object, self.partNum, request_id, code, status))
        
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
                    resp = self.bucket.put_object(self.object, self.buf)
                    return
                except OssError as e:
                    status, code, request_id = e.status, e.code, e.request_id
            
            raise FilesystemError("put object failed. bucket:%s, object:%s, \
                    request_id:%s, code:%s, status:%s" % (self.bucket.bucket_name, \
                    self.object, request_id, code, status))
        
        self.send_buf()
        upload_id = self.get_upload_id()
        retry = self.max_retry_times
        status, code, request_id = "", "", ""
        list_ok = False
        while retry > 0:
            retry -= 1
            try:
                res = self.bucket.list_parts(self.object, upload_id)
                parts = res.parts
                list_ok = True
                break
            except OssError as e:
                status, code, request_id = e.status, e.code, e.request_id
        if not list_ok:
            raise FilesystemError("list parts failed. bucket:%s, object:%s, \
                    request_id:%s, code:%s, status:%s" % (self.bucket.bucket_name, \
                    self.object, request_id, code, status))

        retry = self.max_retry_times
        complete_ok = False
        status, code, request_id = "", "", ""
        while retry > 0:
            retry -= 1
            try:
                resp = self.bucket.complete_multipart_upload(self.object, upload_id, parts)
                complete_ok = True
                break
            except OssError as e:
                status, code, request_id = e.status, e.code, e.request_id
        if not complete_ok:
            raise FilesystemError("complete_multipart_upload failed. bucket:%s, \
                    object:%s, upload_id:%s, request_id:%s, code:%s, status:%s" \
                    % (self.bucket.bucket_name, self.object, upload_id, request_id, code, status))
        self.closed = True
    
    def listdir(self):
        if self.contents:
            return self.contents
        object = self.object
        if object != '' and not object.endswith('/'):
            object = object + '/'
        self.object_list = []
        self.dir_list = []
        for i, object_info in enumerate(oss2.iterators.ObjectIterator(self.bucket, prefix=object, delimiter='/')):
            if object_info.key.endswith('/'):
                self.dir_list.append(object_info.key)
            else:
                self.object_list.append(object_info)
        self.contents = []
        for entry in self.object_list:
            toAdd = entry.key.decode('utf-8')[len(object):]
            last_modified = entry.last_modified
            last_modified_str = datetime.datetime.fromtimestamp(last_modified).strftime('%Y/%m/%d %H:%M:%S')
            self.contents.append((toAdd, entry.size, last_modified_str.decode('utf-8')))
            self.cache_set(self.size_cache, (self.bucket.bucket_name, entry.key), entry.size)
        for entry in self.dir_list:
            toAdd = entry.decode('utf-8')[len(object):]
            self.contents.append((toAdd, -1, 0))
        return self.contents
        
    def isfile(self):
        value = self.cache_get(self.dir_cache, (self.bucket.bucket_name, self.object))
        if value != None:
            return not value
        self.listdir()
        value = (len(self.contents) == 0)
        self.cache_set(self.dir_cache, (self.bucket.bucket_name, self.object), not value)
        return value

    def isdir(self):
        value = self.cache_get(self.dir_cache, (self.bucket.bucket_name, self.object))
        if value != None:
            return value
        value = not self.isfile()
        self.cache_set(self.dir_cache, (self.bucket.bucket_name, self.object), value)
        return value
    
    def cache_get(self, cache, key):
        if cache.has_key(key):
            if cache[key][1] + self.expire_time < time.time():
                return None
            return cache[key][0]
        return None
    
    def cache_set(self, cache, key, value):
        cache[key] = (value, time.time())
    
    def getsize(self):
        value = self.cache_get(self.size_cache, (self.bucket.bucket_name, self.object))
        if value != None:
            return value
        content_len = 0
        try:
            resp = self.bucket.head_object(self.object)
            content_len = resp.headers['content-length']
            self.cache_set(self.size_cache, (self.bucket.bucket_name, self.object), content_len)
        except OssError as e:
            raise FilesystemError("head object failed. bucket:%s, object:%s, \
                    request_id:%s, code:%s, status:%s" % (self.bucket.bucket_name, \
                    self.object, self.request_id, self.code, self.status))
        return content_len
    
    def open_read(self):
        retry = self.max_retry_times
        status, code, request_id = "", "", ""
        while retry > 0:
            retry -= 1
            try:
                resp = self.bucket.get_object(self.object)
                resp.name = self.bucket.bucket_name + '/' + self.object
                resp.closed = False
                def close(self):
                    pass
                resp.close = types.MethodType(close, resp) 
                return resp
            except OssError as e:
                status, code, request_id = e.status, e.code, e.request_id
        raise FilesystemError("get object failed. bucket:%s, object:%s, \
                request_id:%s, code:%s, status:%s" % (self.bucket.bucket_name, \
                self.object, request_id, code, status))
         
    def mkdir(self):
        object = self.object
        if not object.endswith('/'):
            object = object + '/'
        retry = self.max_retry_times
        status, code, request_id = "", "", ""
        while retry > 0:
            retry -= 1
            try:
                resp = self.bucket.put_object(object, "Dir")
                self.cache_set(self.dir_cache, (self.bucket.bucket_name, self.object), True)
                return
            except OssError as e:
                status, code, request_id = e.status, e.code, e.request_id
        raise FilesystemError("put object/dir failed. bucket:%s, object:%s, \
                request_id:%s, code:%s, status:%s" % (self.bucket.bucket_name, \
                object, request_id, code, status))
            
    def rmdir(self):
        object = self.object
        if not object.endswith('/'):
            object = object + '/'
        retry = self.max_retry_times
        status, code, request_id = "", "", ""
        while retry > 0:
            retry -= 1
            try:
                self.bucket.delete_object(object)
                self.cache_set(self.dir_cache, (self.bucket.bucket_name, self.object), False)
                return
            except OssError as e:
                status, code, request_id = e.status, e.code, e.request_id
        raise FilesystemError("delete object/dir failed. bucket:%s, object:%s, \
                request_id:%s, code:%s, status:%s" % (self.bucket.bucket_name, \
                object, request_id, code, status))

    def remove(self):
        object = self.object
        retry = self.max_retry_times
        while retry > 0:
            retry -= 1
            try:
                self.bucket.delete_object(object)
                return
            except OssError as e:
                status, code, request_id = e.status, e.code, e.request_id
        raise FilesystemError("delete object failed. bucket:%s, object:%s, \
                request_id:%s, code:%s, status:%s" % (self.bucket.bucket_name, \
                object, request_id, code, status))
