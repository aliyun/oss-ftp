import logging
import os
import time
from optparse import OptionParser
import ConfigParser

from pyftpdlib.handlers import TLS_FTPHandler
from pyftpdlib.servers import FTPServer
from pyftpdlib.filesystems import AbstractedFS

import ossftp

def start_ftp(masquerade_address, port, internal):

    authorizer = ossftp.OssAuthorizer()
    authorizer.internal = internal
    handler = TLS_FTPHandler
    handler.permit_foreign_addresses = True
    if handler.masquerade_address != "":
        handler.masquerade_address = masquerade_address 
    handler.certfile = 'keycert.pem'
    handler.authorizer = authorizer
    handler.abstracted_fs = ossftp.OssFS
    handler.banner = 'oss ftpd ready.'
    address = ('0.0.0.0', port)
    logging.basicConfig(level=logging.DEBUG)
    server = FTPServer(address, handler)
    server.serve_forever()

def main(args, opts):
    masquerade_address = ""
    port = 990
    internal = None
    if opts.masquerade_address:
        masquerade_address = opts.masquerade_address
    if opts.port:
        try:
            port = (int)(opts.port)
        except ValueError:
            print "invalid FTP port, please input a valid port like --port=990"
            return
    if opts.internal:
        internal = opts.internal
    start_ftp(masquerade_address, port, internal)
    
if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option("", "--masquerade_address", dest="masquerade_address", help="the ip that will reply to FTP Client, then client will send data request to this address.")
    parser.add_option("", "--port", dest="port", help="the local port which ftpserver will listen")
    parser.add_option("", "--internal", dest="internal", help="access oss from internal domain or not")
    (opts, args) = parser.parse_args()
    main(args, opts)
