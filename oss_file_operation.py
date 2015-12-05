from pyftpdlib._compat import PY3, u, unicode, property
import time
import datetime
import pdb
import os

import oss2

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

    def stripFirstDelimiter(self, path):
        while path.startswith('/'):
            path = path[1:]
        return path
    
    def get_upload_id(self):
        try:
            return self.upload_id
        except:
            resp = self.bucket.init_multipart_upload(self.object)
            if resp.status == 200:
                self.upload_id = resp.upload_id
                self.partNum = 0
                return self.upload_id
        return None
    
    def send_buf(self):
        upload_id = self.get_upload_id()
        assert upload_id != None
        if self.buf == '':
            return
        self.partNum += 1
        retry = 3
        while retry > 0:
            retry -= 1
            resp = self.bucket.upload_part(self.object, upload_id, self.partNum, self.buf)
            if resp.status / 100 == 2:
                self.buf = ''
                break
        
    def write(self, data):
        while len(data) + len(self.buf) > self.buflimit:
            _len = self.buflimit - len(self.buf)
            self.buf = self.buf + data[:_len]
            data = data[_len:]
            self.send_buf()
        self.buf += data
        
    def close(self):
        assert self.closed == False
        try:
            self.upload_id
        except:
            retry = 3
            while retry > 0:
                retry -= 1
                resp = self.bucket.put_object(self.object, self.buf)
                if resp.status / 100 == 2:
                    return
            return
        
        self.send_buf()
        upload_id = self.get_upload_id()
        res = self.bucket.list_parts(self.object, upload_id)
        parts = res.parts
        retry = 3
        while retry > 0:
            retry -= 1
            resp = self.bucket.complete_multipart_upload(self.object, upload_id, parts)
            if resp.status / 100 == 2:
                break
        self.closed = True
    
    def listdir(self):
        try:
            return self.contents
        except:
            pass
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
        resp = self.bucket.head_object(self.object)
        content_len = 0
        if (resp.status / 100) == 2:
            content_len = resp.headers['content-length']
            self.cache_set(self.size_cache, (self.bucket.bucket_name, self.object), content_len)
        return content_len
    
    def open_read(self):
        resp = self.bucket.get_object(self.object)
        resp.name = self.bucket.bucket_name + '/' + self.object 
        return resp
     
    def mkdir(self):
        object = self.object
        if not object.endswith('/'):
            object = object + '/'
        resp = self.bucket.put_object(object, "Dir")
        if resp.status/100 != 2:
           print "creating dir %s failed." % object 
        
    def rmdir(self):
        object = self.object
        if not object.endswith('/'):
            object = object + '/'
        self.bucket.delete_object(object)
        
    def remove(self):
        object = self.object
        self.bucket.delete_object(object)
