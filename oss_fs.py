#coding=utf-8
#  ======================================================================
#  Copyright (C) 2007-2013 Giampaolo Rodola' <g.rodola@gmail.com>
#
#                         All Rights Reserved
#
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation
# files (the "Software"), to deal in the Software without
# restriction, including without limitation the rights to use,
# copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following
# conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
# OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.
#
#  ======================================================================

from pyftpdlib.filesystems import AbstractedFS
from oss_fs_impl import *
import sys
import time
import tempfile
import stat
import pdb

from pyftpdlib.filesystems import FilesystemError
from pyftpdlib._compat import PY3, u, unicode, property
_months_map = {1:'Jan', 2:'Feb', 3:'Mar', 4:'Apr', 5:'May', 6:'Jun', 7:'Jul',
               8:'Aug', 9:'Sep', 10:'Oct', 11:'Nov', 12:'Dec'}

class OssFS(AbstractedFS):
    
    def __init__(self, root, cmd_channel):
        AbstractedFS.__init__(self, root, cmd_channel)
        bucket_name = root
        '''
        if not bucket_name.startswith('/'):
            bucket_name = '/' + bucket_name
        if not bucket_name.endswith('/'):
            bucket_name = bucket_name + '/'
        '''
        bucket_name_without_slash = bucket_name
        if bucket_name_without_slash.endswith('/'):
            bucket_name_without_slash = bucket_name_without_slash[:-1]
        if bucket_name_without_slash.startswith('/'):
            bucket_name_without_slash = bucket_name_without_slash[1:]
        bucket_info_dict = cmd_channel.authorizer.get_bucket_info(bucket_name_without_slash)
        access_id, access_key = bucket_info_dict["access_key_dict"].items()[0]
        self.oss_fs_impl = OssFsImpl(bucket_name, bucket_info_dict["endpoint"], access_id, access_key)
    
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
        
    def rename(self, src, dst):
        assert isinstance(src, unicode), src
        assert isinstance(dst, unicode), dst
        self.oss_fs_impl.rename(src, dst)
        
    def chmod(self, path, mode):
        assert isinstance(path, unicode), path
        raise NotImplementedError
    
    def getsize(self, path):
        assert isinstance(path, unicode), path
        return self.oss_fs_impl.getsize(path)
    
    def getmodify(self, path):
        assert isinstance(path, unicode), path
        return self.oss_fs_impl.getmodify(path)
    
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
        SIX_MONTHS = 180 * 24 * 60 * 60
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
                #mtimestr = "Aug 13 03:35"
                mtimestr = "%s %s" % (_months_map[mtime.tm_mon],
                                      time.strftime("%d %H:%M", mtime))
                size = 0
            
            islink = False
            line = "%s %3s %-8s %-8s %8s %s %s\r\n" % (perms, nlinks, uname, gname,
                                                       size, mtimestr, basename)
            yield line.encode('utf8', self.cmd_channel.unicode_errors)
    
    def format_mlsx(self, basedir, listing, perms, facts, ingore_err=True):
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
            line = "%s %s\r\n" % (factstring, basename)
            yield line.encode('utf8', self.cmd_channel.unicode_errors) 
