# -*- coding: utf-8 -*-
import logging
from logging.handlers import RotatingFileHandler
import os
from optparse import OptionParser
from pyftpdlib.handlers import FTPHandler
from pyftpdlib.servers import FTPServer

import ossftp

def set_logger(log_level):
    #log related
    log = "ossftp.log"
    LOGFILE = os.path.join('.', log)
    MAXLOGSIZE = 10*1024*1024 #Bytes
    BACKUPCOUNT = 30
    FORMAT = \
        "%(asctime)s %(levelname)-8s[%(filename)s:%(lineno)d(%(funcName)s)] %(message)s"
    handler = RotatingFileHandler(LOGFILE,
                mode='w',
                maxBytes=MAXLOGSIZE,
                backupCount=BACKUPCOUNT)
    formatter = logging.Formatter(FORMAT)
    handler.setFormatter(formatter)
    logger = logging.getLogger()
    logger.setLevel(log_level)
    logger.addHandler(handler)

def start_ftp(masquerade_address, port, internal, level):

    authorizer = ossftp.OssAuthorizer()
    authorizer.internal = internal
    handler = FTPHandler
    handler.permit_foreign_addresses = True
    if handler.masquerade_address != "":
        handler.masquerade_address = masquerade_address 
    handler.authorizer = authorizer
    handler.abstracted_fs = ossftp.OssFS
    handler.banner = 'oss ftpd ready.'
    address = ('0.0.0.0', port)
    set_logger(level)
    server = FTPServer(address, handler)
    server.serve_forever()

def main(args, opts):
    masquerade_address = ""
    port = 21
    internal = None
    loglevel = "DEBUG"
    if opts.masquerade_address:
        masquerade_address = opts.masquerade_address
    if opts.port:
        try:
            port = int(opts.port)
        except ValueError:
            print "invalid FTP port, please input a valid port like --port=21"
            exit(1)
    if opts.internal:
        internal = opts.internal

    if opts.loglevel:
        loglevel = opts.loglevel
    if loglevel == "DEBUG":
        level = logging.DEBUG
    elif loglevel == "INFO":
        level = logging.INFO
    else:
        print "wrong loglevel parameter: %s" % loglevel
        exit(1)

    start_ftp(masquerade_address, port, internal, level)
    
if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option("", "--masquerade_address", dest="masquerade_address", help="the ip that will reply to FTP Client, then client will send data request to this address.")
    parser.add_option("", "--port", dest="port", help="the local port which ftpserver will listen")
    parser.add_option("", "--internal", dest="internal", help="access oss from internal domain or not")
    parser.add_option("", "--loglevel", dest="loglevel", help="DEBUG/INFO")
    (opts, args) = parser.parse_args()
    main(args, opts)
