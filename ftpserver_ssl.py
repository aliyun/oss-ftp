import logging
import os
import time
from optparse import OptionParser
import ConfigParser

from pyftpdlib.handlers import TLS_FTPHandler
from pyftpdlib.servers import FTPServer
from pyftpdlib.filesystems import AbstractedFS

from oss_authorizers import OssAuthorizer 
from oss_fs import OssFS

CONFIGFILE = os.path.expanduser('~') + '/.oss_ftp.conf'
CONFIGSECTION = 'OSS'
FTP_PORT = 8765

def set_config(filename, endpoint, masquerade_address, port):
    try:
        config = ConfigParser.RawConfigParser()
        config.add_section(CONFIGSECTION)
        config.set(CONFIGSECTION, 'endpoint', endpoint)
        config.set(CONFIGSECTION, 'masquerade_address', masquerade_address)
        config.set(CONFIGSECTION, 'port', str(port))
        cfgfile = open(filename, 'w+')
        config.write(cfgfile)
        cfgfile.close()
        print "Your configuration is saved into %s " % filename 
    except:
        print "config %s exception" % filename

def get_config(filename):
    config = ConfigParser.ConfigParser()
    if not os.path.isfile(filename):
        print "configfile: %s not exsit." % filename
        return "", "", ""
    try:
        config.read(filename)
        endpoint = config.get(CONFIGSECTION, 'endpoint')
        masquerade_address = config.get(CONFIGSECTION, 'masquerade_address')
        port = int(config.get(CONFIGSECTION, 'port'))
    except:
        print "get configuration from %s failed" % filename
    return endpoint, masquerade_address, port

def start_ftp(endpoint, masquerade_address, port):

    authorizer = OssAuthorizer()
    authorizer.endpoint = endpoint
    #handler = FTPHandler
    handler = TLS_FTPHandler
    handler.permit_foreign_addresses = True
    handler.masquerade_address = masquerade_address 
    #handler.passive_ports = (10000, 19999)
    handler.certfile = 'keycert.pem'
    handler.authorizer = authorizer
    handler.abstracted_fs = OssFS
    handler.banner = 'oss ftpd ready.'
    address = ('0.0.0.0', port)
    logging.basicConfig(level=logging.DEBUG)
    server = FTPServer(address, handler)
    server.serve_forever()

def main(args, opts):
    config_file = CONFIGFILE
    if opts.config_file:
        config_file = opts.config_file
    endpoint, masquerade_address, port = get_config(config_file)
    if opts.endpoint:
        endpoint = opts.endpoint
    if opts.masquerade_address:
        masquerade_address = opts.masquerade_address
    if opts.port:
        try:
            port = (int)(opts.port)
        except ValueError:
            print "invalid FTP port, please input a valid port like --ftp_port=2121"
            return
    if "config" in args:
        set_config(config_file, endpoint, masquerade_address, port)
        return
     
    start_ftp(endpoint, masquerade_address, port)
    
if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option("", "--endpoint", dest="endpoint", help="the endpoint which ftpserver will access")
    parser.add_option("", "--masquerade_address", dest="masquerade_address", help="the ip that will reply to FTP Client, then client will send data request to this address.")
    parser.add_option("", "--port", dest="port", help="the local port which ftpserver will listen")
    parser.add_option("", "--config_file", dest="config_file", help="config file")
    (opts, args) = parser.parse_args()
    main(args, opts)
