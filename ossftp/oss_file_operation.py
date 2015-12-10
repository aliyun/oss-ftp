from pyftpdlib._compat import PY3, u, unicode, property
import time
import datetime
import pdb
import os
import types

import oss2
from oss2.exceptions import *

class OssFileOperation:
    size_cache = {}
    dir_cache = {}
    expire_time = 10
    
    def __init__(self, bucket, object):
        self.bucket = bucket 
        self.object = self.stripFirstDelimiter(object)
        self.buf = ''
        self.buflimit = 10 * 1024 * 1024
        self.closed = False
        self.name = self.bucket.bucket_name + '/' + self.object
        self.upload_id = None
        self.max_retry_times = 3
        self.contents = None

    def stripFirstDelimiter(self, path):
        while path.startswith('/'):
            path = path[1:]
        return path
    
    def get_upload_id(self):
        if self.upload_id:
            return self.upload_id
        retry = self.max_retry_times
        while retry > 0:
            retry -= 1
            try:
                resp = self.bucket.init_multipart_upload(self.object)
                self.upload_id = resp.upload_id
                self.partNum = 0
                return self.upload_id
            except OssError as e:
                status = e.status
                code = e.code
                print "init_multipart_upload error, code:%s, status:%s" % (code, status)
        return None

    def send_buf(self):
        upload_id = self.get_upload_id()
        assert upload_id != None
        if self.buf == '':
            return
        self.partNum += 1
        retry = self.max_retry_times
        while retry > 0:
            retry -= 1
            try:
                resp = self.bucket.upload_part(self.object, upload_id, self.partNum, self.buf)
                self.buf = ''
                return
            except OssError as e:
                status = e.status
                code = e.code
                print "upload_part error, code:%s, status:%s" % (code, status)
        
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
            while retry > 0:
                retry -= 1
                try:
                    resp = self.bucket.put_object(self.object, self.buf)
                    return
                except OssError as e:
                    status = e.status
                    code = e.code
                    print "put_object error, code:%s, status:%s" % (code, status)
            return
        
        self.send_buf()
        upload_id = self.get_upload_id()
        retry = self.max_retry_times
        list_ok = False
        while retry > 0:
            retry -= 1
            try:
                res = self.bucket.list_parts(self.object, upload_id)
                parts = res.parts
                list_ok = True
                break
            except OssError as e:
                status = e.status
                code = e.code
                print "list_parts error, code:%s, status:%s" % (code, status)
        if not list_ok:
            print "list failed exceed the max_retry_times"
            return

        retry = self.max_retry_times
        complete_ok = False
        while retry > 0:
            retry -= 1
            try:
                resp = self.bucket.complete_multipart_upload(self.object, upload_id, parts)
                complete_ok = True
                break
            except OssError as e:
                status = e.status
                code = e.code
                print "complete_multipart_upload  error, code:%s, status:%s" % (code, status)
        if not complete_ok:
            print "complete_multipart_upload failed exceed the max_retry_times"
            return
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
            toAdd = entry.key[len(object):].decode('utf-8')
            last_modified = entry.last_modified
            last_modified_str = datetime.datetime.fromtimestamp(last_modified).strftime('%Y/%m/%d %H:%M:%S')
            self.contents.append((toAdd, entry.size, last_modified_str.decode('utf-8')))
            self.cache_set(self.size_cache, (self.bucket.bucket_name, entry.key), entry.size)
        for entry in self.dir_list:
            toAdd = entry[len(object):]
            self.contents.append((toAdd.decode('utf-8'), -1, 0))
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
            status = e.status
            code = e.code
            print "head object failed, code:%s, status:%s" % (code, status)
        return content_len
    
    def open_read(self):
        retry = self.max_retry_times
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
                status = e.status
                code = e.code
                print "get object faild, code: %s, status: %s" % (code, status)
        return None
         
    def mkdir(self):
        object = self.object
        if not object.endswith('/'):
            object = object + '/'
        retry = self.max_retry_times
        while retry > 0:
            retry -= 1
            try:
                resp = self.bucket.put_object(object, "Dir")
            except OssError as e:
                status = e.status
                code = e.code
                print "creating dir %s failed, code:%s, status:%s" % (object, code, status)
            
    def rmdir(self):
        object = self.object
        if not object.endswith('/'):
            object = object + '/'
        retry = self.max_retry_times
        while retry > 0:
            retry -= 1
            try:
                self.bucket.delete_object(object)
            except OssError as e:
                status = e.status
                code = e.code
                print "rm dir %s failed, code:%s, status:%s" % (object, code, status)

    def remove(self):
        object = self.object
        retry = self.max_retry_times
        while retry > 0:
            retry -= 1
            try:
                self.bucket.delete_object(object)
            except OssError as e:
                status = e.status
                code = e.code
                print "rm object %s failed, code:%s, status:%s" % (object, code, status)
