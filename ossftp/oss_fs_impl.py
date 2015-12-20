# -*- coding: utf-8 -*-
from pyftpdlib.filesystems import FilesystemError
import oss2

import oss_file_operation
import defaults

class OssFsImpl:

    def __init__(self, bucket_name, endpoint, access_id, access_key):
        self.bucket_name = bucket_name
        self.endpoint = endpoint
        self.access_id = access_id
        self.access_key = access_key

        self.bucket = oss2.Bucket(oss2.Auth(self.access_id, self.access_key), self.endpoint, self.bucket_name, app_name=defaults.app_name)
        self.size_cache = {}
        self.dir_cache = {}

    def is_bucket(self, path):
        phyPath = path.rstrip('/')
        index = phyPath.rfind('/')
        if index == 0 and not self.is_root(path):
            return True
        return False
    
    def is_root(self, path):
        return path == '/'

    def get_oss_bucket_name(self, path):
        if self.is_root(path):
            return u'/'
        phyPath = path.rstrip('/')
        index = phyPath.find('/', 1)
        if index <= 0:
            return phyPath[1:]
        else:
            return phyPath[1:index]
        
    def get_file_name(self, path):
        if self.is_bucket(path):
            return ""
        if path == '/':
            return u'/'
        bucket = self.get_oss_bucket_name(path)
        return path[len(bucket)+2:]
    
    def get_parent_physical_name(self, path):
        if path == '/':
            return u'/'

        parentPath = path.rstrip('/')

        index = parentPath.rfind('/')
        if index != -1:
            parentPath = parentPath[:index]

        return parentPath

    def normalize_separate_char(self, path):
        normalized_path_name = path.replace('\\', '/')
        return normalized_path_name
    
    def get_physical_name(self, rootDir, curDir, fileName):
        normalizedRootDir = self.normalize_separate_char(rootDir)
        if normalizedRootDir[-1] != '/':
            normalizedRootDir += '/'
        normalized_file_name = self.normalize_separate_char(fileName)
        normalizedCurDir = curDir
        if normalized_file_name[0] != '/':
            if normalizedCurDir == None:
                normalizedCurDir = u'/'
            if normalizedCurDir == '':
                normalizedCurDir = u'/'
            normalizedCurDir = self.normalize_separate_char(normalizedCurDir)
            if normalizedCurDir[0] != '/':
                normalizedCurDir = u'/' + normalizedCurDir
            if normalizedCurDir[-1] != '/':
                normalizedCurDir = normalizedCurDir + '/'
            resArg = normalizedRootDir + normalizedCurDir[1:]
        else:
            resArg = normalizedRootDir

        resArg = resArg.rstrip('/')

        st = normalized_file_name.split('/')
        for tok in st:
            if tok == '':
                continue
            if tok == '.':
                continue
            if tok == '..':
                if resArg.startswith(normalizedRootDir):
                    slashIndex = resArg.rfind('/')
                    if slashIndex != -1:
                        resArg = resArg[0:slashIndex]
                continue
            if tok == '~':
                resArg = normalizedRootDir[:-1]
                continue

            resArg = resArg + '/' + tok

        if len(resArg) + 1 == len(normalizedRootDir):
            resArg = resArg + '/'

        return resArg
   
    def get_bucket(self, path):
        path = self.normalize_separate_char(path)
        bucket_name = self.get_oss_bucket_name(path)
        bucket = oss2.Bucket(oss2.Auth(self.access_id, self.access_key), self.endpoint, bucket_name, app_name=defaults.app_name)
        return bucket
    
    def get_object(self, path):
        path = self.normalize_separate_char(path)
        object = self.get_file_name(path)
        return object

    def get_file_operation_instance(self, path):
        return oss_file_operation.OssFileOperation(self.get_bucket(path), self.get_object(path), self.size_cache, self.dir_cache)

    def open_read(self, path):
        return self.get_file_operation_instance(path).open_read()
    
    def open_write(self, path):
        return self.get_file_operation_instance(path)
    
    def mkdir(self, path):
        return self.get_file_operation_instance(path).mkdir()
        
    def listdir(self, path):
        return self.get_file_operation_instance(path).listdir()
    
    def rmdir(self, path):
        return self.get_file_operation_instance(path).rmdir()
    
    def remove(self, path):
        return self.get_file_operation_instance(path).remove()
    
    def rename(self, path1, path2):
        raise FilesystemError("method rename not implied")
    
    def getsize(self, path):
        return self.get_file_operation_instance(path).getsize()

    def getmodify(self, path):
        raise FilesystemError("method getmodify not implied")
    
    def isfile(self, path):
        return self.get_file_operation_instance(path).isfile()
    
    def isdir(self, path):
        path = self.normalize_separate_char(path)
        if self.is_bucket(path):
            return True
        if self.is_root(path):
            return True
        return self.get_file_operation_instance(path).isdir()
    def lexists(self, path):
        return self.isfile(path) or self.isdir(path)
