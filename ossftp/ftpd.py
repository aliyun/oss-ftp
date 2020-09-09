# -*- coding: utf-8 -*-
import os, sys

current_path = os.path.dirname(os.path.abspath(__file__))
if __name__ == "__main__":

    current_path = os.path.dirname(os.path.abspath(__file__))
    root_path = os.path.abspath( os.path.join(current_path, os.pardir))
    if sys.platform.startswith("linux"):
        python_lib_path = os.path.abspath( os.path.join(root_path, "python27", "unix", "lib"))
        sys.path.append(python_lib_path)
    elif sys.platform == "darwin":
        python_lib_path = os.path.abspath( os.path.join(root_path, "python27", "unix", "lib"))
        sys.path.append(python_lib_path)
        extra_lib = "/System/Library/Frameworks/Python.framework/Versions/2.7/Extras/lib/python/PyObjc"
        sys.path.append(extra_lib)
    elif sys.platform == "win32":
        pass
    else:
        raise RuntimeError("detect platform fail:%s" % sys.platform)

import logging
import threading
from logging.handlers import RotatingFileHandler
import errno
from optparse import OptionParser
from pyftpdlib.handlers import FTPHandler
from pyftpdlib.servers import FTPServer

from oss_authorizers import OssAuthorizer 
from oss_fs import OssFS

class FTPd(threading.Thread):
    """
    A threaded ftp server.
    """
    handler = FTPHandler
    server_class = FTPServer

    def __set_logger(self, log_level):
        work_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
        log_dir = work_dir + '/data/ossftp/'
        try:
            os.makedirs(log_dir)
        except OSError as exc: 
            if exc.errno == errno.EEXIST and os.path.isdir(log_dir):
                pass
            else:
                raise
        LOGFILE = os.path.join(log_dir, "ossftp.log")
        MAXLOGSIZE = 10*1024*1024 #Bytes
        BACKUPCOUNT = 30
        FORMAT = "%(asctime)s %(levelname)-8s[%(filename)s:%(lineno)d(%(funcName)s)] %(message)s"
        handler = RotatingFileHandler(LOGFILE,
                mode='w',
                maxBytes=MAXLOGSIZE,
                backupCount=BACKUPCOUNT)
        formatter = logging.Formatter(FORMAT)
        handler.setFormatter(formatter)
        logger = logging.getLogger()
        if log_level == "DEBUG":
            logger.setLevel(logging.DEBUG)
        elif log_level == "INFO":
            logger.setLevel(logging.INFO)
        elif log_level == "WARNING":
            logger.setLevel(logging.WARNING)
        elif log_level == "ERROR":
            logger.setLevel(logging.ERROR)
        elif log_level == "CRITICAL":
            logger.setLevel(logging.CRITICAL)
        else:
            print "wrong loglevel parameter: %s" % log_level
            exit(1)
        logger.addHandler(handler)

    def __init__(self, masquerade_address, listen_address, port, bucket_endpoints, internal, log_level):
        threading.Thread.__init__(self)
        self.__serving = False
        self.__stopped = False
        self.__lock = threading.Lock()
        self.__flag = threading.Event()

        self.__set_logger(log_level)

        authorizer = OssAuthorizer()
        if bucket_endpoints != "":
            for url in bucket_endpoints.strip().split(','):
                if len(url.split('.', 1)) != 2:
                    print "url:%s format error." % (url)
                    continue
                bucket_name, endpoint = url.split('.', 1)
                authorizer.bucket_endpoints[bucket_name] = endpoint
        authorizer.internal = internal
        self.handler.authorizer = authorizer
        self.handler.permit_foreign_addresses = True
        if self.handler.masquerade_address != "":
            self.handler.masquerade_address = masquerade_address 
        self.handler.abstracted_fs = OssFS
        self.handler.banner = 'oss ftpd ready.'
        # lower buffer sizes = more "loops" while transfering data
        # = less false positives
        self.handler.dtp_handler.ac_in_buffer_size = 4096
        self.handler.dtp_handler.ac_out_buffer_size = 4096
        address = (listen_address, port)
        self.server = self.server_class(address, self.handler)

    def __repr__(self):
        status = [self.__class__.__module__ + "." + self.__class__.__name__]
        if self.__serving:
            status.append('active')
        else:
            status.append('inactive')
        status.append('%s:%s' % self.server.socket.getsockname()[:2])
        return '<%s at %#x>' % (' '.join(status), id(self))

    def start(self, timeout = 0.1):
        """
        Start serving until an explicit stop() request.
        Polls for shutdown every 'timeout' seconds.
        """
        if self.__serving:
            raise RuntimeError("ossftp server already started!")
        if self.__stopped:
            # ensure the server can be started again
            FTPd.__init__(self, self.server.socket.getsockname(), self.handler)
        self.__timeout = timeout
        threading.Thread.start(self)
        self.__flag.wait()

    def run(self):
        self.__serving = True
        self.__flag.set()
        while self.__serving:
            self.__lock.acquire()
            self.server.serve_forever(timeout=self.__timeout, blocking=False)
            self.__lock.release()
        self.server.close_all()

    def stop(self):
        """
        Stop serving (also disconnecting all currently connected
        clients) by telling the serve_forever() loop to stop and
        waits until it does.
        """
        if not self.__serving:
            raise RuntimeError("ossftp server not started yet!")
        self.__serving = False
        self.__stopped = True
        self.join()

