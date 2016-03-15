# -*- coding: utf-8 -*-
import os
import time

from pyftpdlib.filesystems import FilesystemError
from pyftpdlib._compat import PY3, u, unicode
_months_map = {1:'Jan', 2:'Feb', 3:'Mar', 4:'Apr', 5:'May', 6:'Jun', 7:'Jul',
               8:'Aug', 9:'Sep', 10:'Oct', 11:'Nov', 12:'Dec'}
from pyftpdlib.filesystems import AbstractedFS

import oss_fs_impl 

class OssFS(AbstractedFS):
    
    def __init__(self, root, cmd_channel):
        assert isinstance(root, unicode), root
        AbstractedFS.__init__(self, root, cmd_channel)
        bucket_name = root.strip('/')
        bucket_info = cmd_channel.authorizer.get_bucket_info(bucket_name)
        access_key_id, access_key_secret= bucket_info.access_key.items()[0]
        endpoint = bucket_info.endpoint
        self.oss_fs_impl = oss_fs_impl.OssFsImpl(bucket_name, endpoint, access_key_id, access_key_secret)
    
    def open(self, filename, mode):
        assert isinstance(filename, unicode), filename
        if mode.startswith('r') or mode.startswith('R'):
            return self.oss_fs_impl.open_read(filename)
        else:
            return self.oss_fs_impl.open_write(filename)
    
    def chdir(self, path):
        assert isinstance(path, unicode), path
        if not self.isdir(path):
            raise FilesystemError, 'Not a dir.'
        path = path.replace('\\', '/')
        if not path.startswith(self.root):
            path = u'/'
        else:
            path = path[len(self.root):]
        if path == "":
            path = u'/'
        if not path.startswith('/'):
            path = '/' + path
        self._cwd = path
    
    def mkdir(self, path):
        assert isinstance(path, unicode), path
        self.oss_fs_impl.mkdir(path)
        
    def listdir(self, path):
        assert isinstance(path, unicode), path
        return self.oss_fs_impl.listdir(path)
        
    def rmdir(self, path):
        assert isinstance(path, unicode), path
        self.oss_fs_impl.rmdir(path)
        
    def remove(self, path):
        assert isinstance(path, unicode), path
        self.oss_fs_impl.remove(path)
    
    def lexists(self, path):
        assert isinstance(path, unicode), path
        return self.oss_fs_impl.lexists(path)
    '''
    def realpath(self, path):
        assert isinstance(path, unicode), path
        return path
    '''

    def rename(self, src, dst):
        assert isinstance(src, unicode), src
        assert isinstance(dst, unicode), dst
        self.oss_fs_impl.rename(src, dst)
        
    def chmod(self, path, mode):
        assert isinstance(path, unicode), path
        raise FilesystemError("method chmod is not implied") 
    
    def getsize(self, path):
        assert isinstance(path, unicode), path
        return self.oss_fs_impl.getsize(path)
    
    def getmtime(self, path):
        assert isinstance(path, unicode), path
        return self.oss_fs_impl.getmtime(path)
    
    def stat(self, path):
        return ""
    
    def isfile(self, path):
        assert isinstance(path, unicode), path
        return self.oss_fs_impl.isfile(path)
    
    def isdir(self, path):
        assert isinstance(path, unicode), path
        return self.oss_fs_impl.isdir(path)
    
    def get_list_dir(self, path):
        assert isinstance(path, unicode), path
        if self.isdir(path):
            listing = self.listdir(path)
            try:
                listing.sort()
            except UnicodeDecodeError:
                pass
            return self.format_list(path, listing)
        else:
            basedir, filename = os.path.split(path)
            return self.format_list(basedir, [(filename, 0, 0)])
        
    def format_list(self, basedir, listing, ignore_err=True):
        assert isinstance(basedir, unicode), basedir
        if listing:
            assert isinstance(listing[0][0], unicode)
        if self.cmd_channel.use_gmt_times:
            timefunc = time.gmtime
        else:
            timefunc = time.localtime
        now = time.time()
        for (basename, size, modify) in listing:
            if basename == '':
                continue
            file = os.path.join(basedir, basename)
            isdir = file.endswith('/')
            if isdir:
                perms = 'drwxrwxrwx'
            else:
                perms = '-rw-rw-rw-'
            nlinks = 1
            uname = 'owner'
            gname = 'group'
            mtime = timefunc(now)
            mtimestr = "Aug 13 03:35"
            if not isdir:
                mtimestr = "%s %s" % (_months_map[int(modify[5:7])],
                                      "%s %s:%s" % (modify[2:4], modify[11:13], modify[14:16]))
            else:
                mtimestr = "%s %s" % (_months_map[mtime.tm_mon],
                                      time.strftime("%d %H:%M", mtime))
                size = 0
            
            line = "%s %3s %-8s %-8s %8s %s %s\r\n" % (perms, nlinks, uname, gname,
                                                       size, mtimestr, basename.rstrip('/'))
            yield line.encode('utf8', self.cmd_channel.unicode_errors)
    
    def format_mlsx(self, basedir, listing, perms, facts, ignore_err=True):
        assert isinstance(basedir, unicode), basedir
        if listing:
            assert isinstance(listing[0][0], unicode)
        if self.cmd_channel.use_gmt_times:
            timefunc = time.gmtime
        else:
            timefunc = time.localtime
        permdir = ''.join([x for x in perms if x not in 'arw'])
        permfile = ''.join([x for x in perms if x not in 'celmp'])
        if ('w' in perms) or ('a' in perms) or ('f' in perms):
            permdir += 'c'
        if 'd' in perms:
            permdir += 'p'
        show_type = 'type' in facts
        show_perm = 'perm' in facts
        show_size = 'size' in facts
        show_modify = 'modify' in facts
        show_create = 'create' in facts
        show_mode = 'unix.mode' in facts
        show_uid = 'unix.uid' in facts
        show_gid = 'unix.gid' in facts
        show_unique = 'unique' in facts
        for (basename, size, modify) in listing:
            if basename == '':
                continue
            retfacts = dict()
            file = os.path.join(basedir, basename)
            isdir = file.endswith('/')
            if isdir:
                if show_type:
                    if basename == '.':
                        retfacts['type'] = 'cdir'
                    elif basename == '..':
                        retfacts['type'] = 'pdir'
                    else:
                        retfacts['type'] = 'dir'
                if show_perm:
                    retfacts['perm'] = permdir
            else:
                if show_type:
                    retfacts['type'] = 'file'
                if show_perm:
                    retfacts['perm'] = permfile
            if show_size and not isdir:
                retfacts['size'] = size
            # last modification time
            if not isdir:
                retfacts['modify'] = modify[:4] + modify[5:7] + modify[8:10] + modify[11:13] + modify[14:16] + modify[17:19]
            factstring = "".join(["%s=%s;" % (x, retfacts[x]) \
                                  for x in sorted(retfacts.keys())])
            line = "%s %s\r\n" % (factstring, basename.rstrip('/'))
            yield line.encode('utf8', self.cmd_channel.unicode_errors) 
