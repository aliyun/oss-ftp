# -*- coding: utf-8 -*-

import sys
import os
import logging
from logging.handlers import RotatingFileHandler
import platform

current_path = os.path.dirname(os.path.abspath(__file__))
root_path = os.path.abspath( os.path.join(current_path, os.pardir))
if root_path not in sys.path:
    sys.path.append(root_path)

if sys.platform.startswith("linux"):
    python_lib_path = None
    if (platform.architecture()[0] == '32bit'):
        python_lib_path = os.path.abspath( os.path.join(root_path, "python27", "unix", "lib32"))
    else:
        python_lib_path = os.path.abspath( os.path.join(root_path, "python27", "unix", "lib64"))
    sys.path.append(python_lib_path)

elif sys.platform == "darwin":
    python_lib_path = os.path.abspath( os.path.join(root_path, "python27", "macos", "lib"))
    sys.path.append(python_lib_path)
    extra_lib = "/System/Library/Frameworks/Python.framework/Versions/2.7/Extras/lib/python/PyObjc"
    sys.path.append(extra_lib)
elif sys.platform == "win32":
    pass
else:
    raise RuntimeError("detect platform fail:%s" % sys.platform)

import paramiko
import errno
import time
import optparse
import oss2
import stat
import requests
from paramiko import SFTP_OK, SFTP_OP_UNSUPPORTED, SFTP_FAILURE
from paramiko import SFTPError
from sftp_authorizer import OssSftpAuthServer
from oss2.compat import is_py3


if is_py3:
    import socketserver as SocketServer
else:
    import SocketServer

def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc:
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise

def set_logger(level):
    work_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
    log_dir = work_dir + '/data/osssftp/'
    mkdir_p(log_dir)
    LOGFILE = log_dir + "osssftp.log"
    FORMAT = "%(asctime)s %(levelname)-8s[%(filename)s:%(lineno)d(%(funcName)s)] %(message)s"
    MAXLOGSIZE = 10*1024*1024 #Bytes
    BACKUPCOUNT = 30
    handler = RotatingFileHandler(LOGFILE,
                mode='w',
                maxBytes=MAXLOGSIZE,
                backupCount=BACKUPCOUNT)
    formatter = logging.Formatter(FORMAT)
    handler.setFormatter(formatter)
    logger = logging.getLogger()
    logger.setLevel(level)
    logger.addHandler(handler)


# Before the sftp client connecting, used debug level, and after connecting use a new level.
set_logger("DEBUG")
_logger = logging.getLogger(__name__)

# upload part size, unit is MB. the smaller file will use put_object method, and the bigger file will use upload_part method.
_buff_size = 10
MAX_RETRIES = 3

def retry(fn):
    def wrapper(*args, **kwargs):
        oss_file_op_intance = args[0]
        retry = MAX_RETRIES
        status, code, message, request_id = None, "", "", ""
        while retry > 0:
            retry -= 1
            try:
                return fn(*args, **kwargs)
            except oss2.exceptions.OssError as e:
                status, code, message, request_id = e.status, e.code, e.message, e.request_id
        raise SFTPError("%s failed. bucket:%s, key:%s,\
            request_id:%s, code:%s, status:%s, message:%s" % (fn.__name__,
            oss_file_op_intance.bucket.bucket_name, oss_file_op_intance.key,
            request_id, code, status, message))
    return wrapper

class OssSftpHandle(paramiko.SFTPHandle):
    def __init__(self, bucket, key, flags):
        self.bucket = bucket
        self.key = key
        self.flags = flags
        self.obj = None
        self.upload_id = None
        self.part_num = 0
        self.part_list = []
        self.buf = b''
        self.buflimit = _buff_size * 1024 * 1024
        self.logger = _logger
        self.logger.debug('buff_size:%d' % self.buflimit)
        self.last_offset = None
        self.end_flag = False

        if self.flags == os.O_RDONLY:
            self.obj = self.get_object(key)

    def stat(self):
        return SFTP_OP_UNSUPPORTED

    def chattr(self, attr):
        return SFTP_OP_UNSUPPORTED

    @retry
    def get_object(self, key):
        return self.bucket.get_object(key)

    @retry
    def put_object(self, key, buf):
        self.bucket.put_object(key, buf)

    @retry
    def init_multipart_upload(self, key):
        return self.bucket.init_multipart_upload(key)

    @retry
    def upload_part(self, key, upload_id, part_num, buf):
        return self.bucket.upload_part(key, upload_id, part_num, buf)

    @retry
    def complete_multipart_upload(self, key, upload_id, part_list):
        self.bucket.complete_multipart_upload(key, upload_id, part_list)

    def read(self, offset, length):
        # Some sftp client tools like FinalShell maybe read the lower offset after reading eof many times.
        # The worse networking environment maybe cause reading data repeatedly, but the read-obj does'nt support it.
        if self.end_flag is False and self.last_offset is not None and offset < self.last_offset:
            _logger.error('Not allowing to get data repeatedly, your networking environment might be worse.')
            return SFTP_FAILURE

        self.last_offset = offset

        # Some versions of library maybe not support reading eof repeatedly.
        try:
            data = self.obj.read(length)
            if len(data) == 0:
                self.end_flag = True
            return data
        except requests.exceptions.StreamConsumedError:
            pass
        return ''

    def _send_buf(self):
        if not self.buf:
            return

        if self.upload_id is None:
            self.upload_id = self.init_multipart_upload(self.key).upload_id

        self.part_num += 1
        time1 = time.time()
        res = self.upload_part(self.key, self.upload_id, self.part_num, self.buf)
        time2 = time.time()
        self.logger.debug('upload cost %d ' % (time2 - time1))
        self.buf = b''
        self.part_list.append(oss2.models.PartInfo(self.part_num, res.etag))

    def write(self, offset, data):
        while len(data) + len(self.buf) > self.buflimit:
            _len = self.buflimit - len(self.buf)
            self.buf = self.buf + data[:_len]
            data = data[_len:]
            self._send_buf()
        self.buf += data

        return SFTP_OK

    def close(self):
        if self.flags == os.O_RDONLY:
            return
        if len(self.part_list) == 0:
            self.put_object(self.key, self.buf)
        else:
            self._send_buf()
            self.complete_multipart_upload(self.key, self.upload_id, self.part_list)


class OssSftpServerInterface(paramiko.SFTPServerInterface):
    def __init__(self, ddd, auth):
        self.auth = auth
        self.bucket = auth.bucket
        self.home_dir = auth.home_dir

    def _convert_to_oss_path(self, path):
        if path.startswith('/'):
            path = path[1:]
        return path

    def list_folder(self, path):
        compat_path = self.make_compat_path(path)

        if self.home_dir != '':
            if compat_path == '/':
                compat_path = '/' + self.home_dir
            else:
                compat_path = '/' + self.home_dir + compat_path

        out = []
        prefix = self._convert_to_oss_path(compat_path)
        prefix = prefix + '/' if prefix != '' else prefix

        for obj in oss2.ObjectIterator(self.bucket, delimiter='/', prefix=prefix):
            if obj.last_modified is None:
                attr = paramiko.SFTPAttributes()
                attr.filename = obj.key
                attr.filename = attr.filename[len(prefix):]
                attr.filename = attr.filename[:-1]
                attr.st_mode = (stat.S_IFDIR | stat.S_IREAD | stat.S_IWRITE)
                attr.st_mtime = attr.st_atime
                out.append(attr)
            else:
                if obj.key.endswith('/'):
                    continue
                attr = paramiko.SFTPAttributes()
                attr.filename = obj.key
                attr.filename = attr.filename[len(prefix):]
                attr.st_mode = (stat.S_IFREG | stat.S_IREAD | stat.S_IWRITE)
                attr.st_atime = int(obj.last_modified)
                attr.st_mtime = attr.st_atime
                attr.st_size = obj.size
                out.append(attr)

        return out

    def stat(self, path):
        compat_path = self.make_compat_path(path)

        if self.home_dir != '':
            if compat_path == '/':
                compat_path = '/' + self.home_dir
            else:
                compat_path = '/' + self.home_dir + compat_path

        oss_path = self._convert_to_oss_path(compat_path)
        prefix = oss_path + '/' if oss_path != '' else oss_path

        is_dir = False
        try:
            result = self.bucket.list_objects(prefix=prefix, max_keys=1)
            if len(result.object_list) > 0:
                is_dir = True
        except:
            return SFTP_FAILURE

        if is_dir is True:
            attr = paramiko.SFTPAttributes()
            attr.filename = path
            attr.st_mode = (stat.S_IFDIR | stat.S_IREAD | stat.S_IWRITE)
            return attr
        else:
            # make compatible with touch file situation.
            length = 0
            try:
                head_result = self.bucket.head_object(oss_path)
                length = head_result.content_length
            except:
                pass
            attr = paramiko.SFTPAttributes()
            attr.filename = path
            attr.st_mode = (stat.S_IFREG | stat.S_IREAD | stat.S_IWRITE)
            attr.st_size = length
            return attr

    def lstat(self, path):
        return self.stat(path)

    def open(self, path, flags, attr):
        compat_path = self.make_compat_path(path)

        if self.home_dir != '':
            compat_path = '/' + self.home_dir + compat_path

        object_name = self._convert_to_oss_path(compat_path)
        return OssSftpHandle(self.bucket, object_name, flags)

    def remove(self, path):
        compat_path = self.make_compat_path(path)

        if self.home_dir != '':
            compat_path = '/' + self.home_dir + compat_path

        object_name = self._convert_to_oss_path(compat_path)
        self.bucket.delete_object(object_name)
        return SFTP_OK

    def mkdir(self, path, attr):
        compat_path = self.make_compat_path(path)

        if self.home_dir != '':
            compat_path = '/' + self.home_dir + compat_path

        object_name = self._convert_to_oss_path(compat_path) + '/'

        self.bucket.put_object(object_name, '')
        return SFTP_OK

    def rmdir(self, path):
        compat_path = self.make_compat_path(path)

        if self.home_dir != '':
            compat_path = '/' + self.home_dir + compat_path

        oss_path = self._convert_to_oss_path(compat_path) + '/'

        try:
            result = self.bucket.get_bucket_info()
            if result.versioning_status in [oss2.BUCKET_VERSIONING_ENABLE, oss2.BUCKET_VERSIONING_SUSPEND]:
                next_key_marker = None
                next_versionid_marker = None
                is_truncated = True
                while is_truncated is True:
                    objects = self.bucket.list_object_versions(prefix=oss_path, key_marker=next_key_marker,
                                                          versionid_marker=next_versionid_marker)
                    for obj in objects.versions:
                        self.bucket.delete_object(obj.key, params={'versionId': obj.versionid})
                    for del_marker in objects.delete_marker:
                        self.bucket.delete_object(del_marker.key, params={'versionId': del_marker.versionid})
                    is_truncated = objects.is_truncated
                    if is_truncated:
                        next_key_marker = objects.next_key_marker
                        next_versionid_marker = objects.next_versionid_marker
        except:
            pass

        for up in oss2.MultipartUploadIterator(self.bucket, prefix=oss_path):
            self.bucket.abort_multipart_upload(up.key, up.upload_id)

        for obj in oss2.ObjectIterator(self.bucket, prefix=oss_path):
            self.bucket.delete_object(obj.key)

        # lower version not support live channel.
        try:
            for ch_iter in oss2.LiveChannelIterator(self.bucket, prefix=oss_path):
                self.bucket.delete_live_channel(ch_iter.name)
        except:
            pass

        return paramiko.SFTP_OK

    def rename(self, oldpath, newpath):
        return paramiko.SFTP_OP_UNSUPPORTED

    def chattr(self, path, attr):
        # make compat with Winscp.
        return paramiko.SFTP_OK

    def symlink(self, target_path, path):
        return paramiko.SFTP_OP_UNSUPPORTED

    def readlink(self, path):
        return paramiko.SFTP_OP_UNSUPPORTED

    def make_compat_path(self, path):
        # make compat with sftp command
        compat_path = path
        if not path.startswith('/'):
            compat_path = '/' + path
        return compat_path



class SFTPConnectionRequestHandler(SocketServer.BaseRequestHandler):
    def handle(self):
        set_logger(self.server.loglevel.upper())
        transport = paramiko.Transport(self.request)
        host_key = paramiko.RSAKey.from_private_key_file(self.server.keyfile)
        transport.add_server_key(host_key)

        authorizer = OssSftpAuthServer()
        if self.server.bucket_endpoints != "" and self.server.bucket_endpoints is not None:
            for url in self.server.bucket_endpoints.strip().split(','):
                if len(url.split('.', 1)) != 2:
                    _logger.error("url:%s format error." % url)
                    continue
                bucket_name, endpoint = url.split('.', 1)
                authorizer.bucket_endpoints[bucket_name] = endpoint
        authorizer.internal = self.server.internal
        authorizer.protocol = self.server.protocol

        transport.set_subsystem_handler('sftp', paramiko.SFTPServer, OssSftpServerInterface, authorizer)
        transport.start_server(server=authorizer)

        ch = transport.accept(20)
        if ch is None:
            return

        transport.join()


class SFTPServer(SocketServer.ThreadingTCPServer):
    def __init__(self, listen_address, port, loglevel, bucket_endpoints, internal, keyfile, protocol):
        self.listen_address = listen_address
        self.port = port
        self.loglevel = loglevel
        self.bucket_endpoints = bucket_endpoints
        self.internal = internal
        self.keyfile = keyfile
        self.protocol = protocol
        self.allow_reuse_address = True
        try:
            SocketServer.TCPServer.__init__(self, (listen_address, port), SFTPConnectionRequestHandler)
        except Exception as e:
            _logger.error(e)
            raise e


def start_sftp(listen_address, port, loglevel, bucket_endpoints, internal, keyfile, buff_size, protocol):
    if not os.path.exists(keyfile):
        _logger.info('SSH key file has not specified, generating 2048-bit RSA key :{0}'.format(keyfile))
        rsa_key = paramiko.RSAKey.generate(bits=2048)
        rsa_key.write_private_key_file(keyfile)

    global _buff_size
    _buff_size = int(buff_size)
    _logger.debug('sftp server start...')
    server = SFTPServer(listen_address, port, loglevel, bucket_endpoints, internal, keyfile, protocol)
    server.serve_forever()


if __name__ == '__main__':
    parser = optparse.OptionParser()

    parser.add_option("", "--listen_address", dest="listen_address", default='127.0.0.1',
                      help="the address which ftpserver will listen, default is 127.0.0.1")
    parser.add_option("", "--port", dest="port", type='int', default='50000', help="the local port which ftpserver will listen, default is 50000.")
    parser.add_option("", "--buff_size", dest="buff_size", type='int', default='10', help="the buff size is used for send data, default is 10, unit is MB.")
    parser.add_option("", "--loglevel", dest="loglevel", default='INFO', help="DEBUG/INFO/, default is INFO.")
    parser.add_option("", "--bucket_endpoints", dest="bucket_endpoints", help="use this endpoint to access oss.")
    parser.add_option("", "--internal", dest="internal", help="access oss from internal domain or not.")
    parser.add_option("", '--keyfile', dest='keyfile', default='sftp_rsa',
                      help='RSA server key file (defaults to %default, generated if missing)')
    parser.add_option("", "--protocol", dest="protocol", default='https', help="https/http, default is https.")

    options, args = parser.parse_args()

    start_sftp(options.listen_address, options.port, options.loglevel,
               options.bucket_endpoints, options.internal,  options.keyfile, options.buff_size, options.protocol)
