#!/usr/bin/env python coding:utf-8

import os, sys
import re
import SocketServer, socket, ssl
import BaseHTTPServer
import errno
import urlparse
import threading
import urllib2
import time
import datetime
from xlog import LogFileTailer

current_path = os.path.dirname(os.path.abspath(__file__))
root_path = os.path.abspath(os.path.join(current_path, os.pardir))
ossftp_log_path = os.path.join(root_path, "data", "ossftp", "ossftp.log")
ossftp_log_tailer = LogFileTailer(ossftp_log_path)

import json
import launcher_log
import module_init
import config
import autorun


NetWorkIOError = (socket.error, ssl.SSLError, OSError)



class LocalServer(SocketServer.ThreadingTCPServer):
    allow_reuse_address = True

    def close_request(self, request):
        try:
            request.close()
        except Exception:
            pass

    def finish_request(self, request, client_address):
        try:
            self.RequestHandlerClass(request, client_address, self)
        except NetWorkIOError as e:
            if e[0] not in (errno.ECONNABORTED, errno.ECONNRESET, errno.EPIPE):
                raise

    def handle_error(self, *args):
        """make ThreadingTCPServer happy"""
        etype, value = sys.exc_info()[:2]
        if isinstance(value, NetWorkIOError) and 'bad write retry' in value.args[1]:
            etype = value = None
        else:
            del etype, value
            SocketServer.ThreadingTCPServer.handle_error(self, *args)

module_menus = {}
class Http_Handler(BaseHTTPServer.BaseHTTPRequestHandler):
    deploy_proc = None


    def load_module_menus(self):
        global module_menus
        module_menus = {}
        #config.load()
        modules = config.get(['modules'], None)
        for module in modules:
            values = modules[module]
            if module != "launcher" and config.get(["modules", module, "auto_start"], 0) != 1:
                continue

            #version = values["current_version"]
            menu_path = os.path.join(root_path, module, "web_ui", "menu.json")
            if not os.path.isfile(menu_path):
                continue
                
            module_menu = json.load(file(menu_path, 'r'))          
            module_menus[module] = module_menu

        module_menus = sorted(module_menus.iteritems(), key=lambda (k,v): (v['menu_sort_id']))
        #for k,v in self.module_menus:
        #    logging.debug("m:%s id:%d", k, v['menu_sort_id'])

    def address_string(self):
        return '%s:%s' % self.client_address[:2]

    def send_response(self, mimetype, data):
        self.wfile.write(('HTTP/1.1 200\r\nAccess-Control-Allow-Origin: *\r\nContent-Type: %s\r\nContent-Length: %s\r\n\r\n' % (mimetype, len(data))).encode())
        self.wfile.write(data)
    def send_not_found(self):
        self.wfile.write(b'HTTP/1.1 404\r\nContent-Type: text/plain\r\nConnection: close\r\n\r\n404 Not Found')
    def do_POST(self):
        #url_path = urlparse.urlparse(self.path).path
        url_path_list = self.path.split('/')
        if len(url_path_list) >= 3 and url_path_list[1] == "module":
            module = url_path_list[2]
            if len(url_path_list) >= 4 and url_path_list[3] == "control":
                if module not in module_init.proc_handler:
                    launcher_log.warn("request %s no module in path", self.path)
                    self.send_not_found()
                    return

                path = '/' + '/'.join(url_path_list[4:])
                controler = module_init.proc_handler[module]["imp"].local.web_control.ControlHandler(self.client_address, self.headers, self.command, path, self.rfile, self.wfile)
                controler.do_POST()
                return

    def do_GET(self):
        try:
            refer = self.headers.getheader('Referer')
            netloc = urlparse.urlparse(refer).netloc
            if not netloc.startswith("127.0.0.1") and not netloc.startswitch("localhost"):
                launcher_log.warn("web control ref:%s refuse", netloc)
                return
        except:
            pass

        # check for '..', which will leak file
        if re.search(r'(\.{2})', self.path) is not None:
            self.wfile.write(b'HTTP/1.1 404\r\n\r\n')
            launcher_log.warn('%s %s %s haking', self.address_string(), self.command, self.path )
            return

        url_path = urlparse.urlparse(self.path).path
        if url_path == '/':
            return self.req_index_handler()

        url_path_list = self.path.split('/')
        if len(url_path_list) >= 3 and url_path_list[1] == "module":
            module = url_path_list[2]
            if len(url_path_list) >= 4 and url_path_list[3] == "control":
                if module not in module_init.proc_handler:
                    launcher_log.warn("request %s no module in path", url_path)
                    self.send_not_found()
                    return

                path = '/' + '/'.join(url_path_list[4:])
                controler = module_init.proc_handler[module]["imp"].local.web_control.ControlHandler(self.client_address, self.headers, self.command, path, self.rfile, self.wfile)
                controler.do_GET()
                return
            else:
                file_path = os.path.join(root_path, module, url_path_list[3:].join('/'))
        else:
            file_path = os.path.join(current_path, 'web_ui' + url_path)


        launcher_log.debug ('launcher web_control %s %s %s ', self.address_string(), self.command, self.path)
        if os.path.isfile(file_path):
            if file_path.endswith('.js'):
                mimetype = 'application/javascript'
            elif file_path.endswith('.css'):
                mimetype = 'text/css'
            elif file_path.endswith('.html'):
                mimetype = 'text/html'
            elif file_path.endswith('.jpg'):
                mimetype = 'image/jpeg'
            elif file_path.endswith('.png'):
                mimetype = 'image/png'
            else:
                mimetype = 'text/plain'

            self.send_file(file_path, mimetype)
        elif url_path == '/config':
            self.req_config_handler()
        elif url_path == '/log':
            self.req_log_handler()
        elif url_path == '/download':
            self.req_download_handler()
        elif url_path == '/init_module':
            self.req_init_module_handler()
        elif url_path == '/quit':
            self.send_response('text/html', '{"status":"success"}')
            module_init.stop_all()
            os._exit(0)
        elif url_path == '/restart':
            self.send_response('text/html', '{"status":"success"}')
            module_init.stop_all()
            module_init.start_all_auto()
        else:
            self.wfile.write(b'HTTP/1.1 404\r\nContent-Type: text/plain\r\nConnection: close\r\n\r\n404 Not Found')
            launcher_log.info('%s "%s %s HTTP/1.1" 404 -', self.address_string(), self.command, self.path)

    def send_file(self, filename, mimetype):
        try:
            with open(filename, 'rb') as fp:
                data = fp.read()
            tme = (datetime.datetime.today()+datetime.timedelta(minutes=330)).strftime('%a, %d %b %Y %H:%M:%S GMT')
            self.wfile.write(('HTTP/1.1 200\r\nAccess-Control-Allow-Origin: *\r\nCache-Control:public, max-age=31536000\r\nExpires: %s\r\nContent-Type: %s\r\nContent-Length: %s\r\n\r\n' % (tme, mimetype, len(data))).encode())
            self.wfile.write(data)
        except:
            self.wfile.write(b'HTTP/1.1 404\r\nContent-Type: text/plain\r\nConnection: close\r\n\r\n404 Open file fail')

    def req_index_handler(self):
        req = urlparse.urlparse(self.path).query
        reqs = urlparse.parse_qs(req, keep_blank_values=True)

        try:
            target_module = reqs['module'][0]
            target_menu = reqs['menu'][0]
        except:
            target_module = 'launcher'
            target_menu = 'config'


        if len(module_menus) == 0:
            self.load_module_menus()

        index_path = os.path.join(current_path, 'web_ui', "index.html")
        with open(index_path, "r") as f:
            index_content = f.read()

        menu_content = ''
        for module,v in module_menus:
            #logging.debug("m:%s id:%d", module, v['menu_sort_id'])
            title = v["module_title"]
            menu_content += '<li class="nav-header">%s</li>\n' % title
            for sub_id in sorted(v['sub_menus']):
                sub_title = v['sub_menus'][sub_id]['title']
                sub_url = v['sub_menus'][sub_id]['url']
                if target_module == title and target_menu == sub_url:
                    active = 'class="active"'
                else:
                    active = ''
                menu_content += '<li %s><a href="/?module=%s&menu=%s">%s</a></li>\n' % (active, module, sub_url, sub_title)

        right_content_file = os.path.join(root_path, target_module, "web_ui", target_menu + ".html")
        if os.path.isfile(right_content_file):
            with open(right_content_file, "r") as f:
                right_content = f.read()
        else:
            right_content = ""

        data = (index_content.decode('utf-8') % (menu_content, right_content.decode('utf-8') )).encode('utf-8')
        self.send_response('text/html', data)
    
    def ip_check(self, ip_str):
        pattern = r"\b(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b"
        if re.match(pattern, ip_str):
            return True
        else:
            return False

    def req_config_handler(self):
        req = urlparse.urlparse(self.path).query
        reqs = urlparse.parse_qs(req, keep_blank_values=True)
        data = ''        

        if reqs['cmd'] == ['get_config']:
            config.load()
            data = '{ "popup_webui": %d, "show_systray": %d, "auto_start": %d, "ossftp_address": "%s", "ossftp_port": %d, "ossftp_loglevel": "%s", "ossftp_bucketendpoints": "%s" }' %\
                   (config.get(["modules", "launcher", "popup_webui"], 1)
                    , config.get(["modules", "launcher", "show_systray"], 1)
                    , config.get(["modules", "launcher", "auto_start"], 0)
                    , config.get(["modules", "ossftp", "address"], '127.0.0.1')
                    , config.get(["modules", "ossftp", "port"], 2048)
                    , config.get(["modules", "ossftp", "log_level"], 'INFO')
                    , config.get(["modules", "ossftp", "bucket_endpoints"], ''))
        elif reqs['cmd'] == ['set_config']:
            success = True
            popup_webui = config.get(["modules", "launcher", "popup_webui"], 1)
            auto_start = config.get(["modules", "launcher", "auto_start"], 0)
            show_systray = config.get(["modules", "launcher", "show_systray"], 1)
            ossftp_address = config.get(["modules", "ossftp", "address"], "127.0.0.1")
            ossftp_port = config.get(["modules", "ossftp", "port"], 2048)
            ossftp_loglevel = config.get(["modules", "ossftp", "log_level"], 'INFO')
            ossftp_bucketendpoints = config.get(["modules", "ossftp", "bucket_endpoints"], '')
            data = '{"res":"fail"}'
            if success and 'popup_webui' in reqs :
                popup_webui = int(reqs['popup_webui'][0])
                if popup_webui != 0 and popup_webui != 1:
                    success = False
                    data = '{"res":"fail, popup_webui:%s"}' % popup_webui
            if success and 'show_systray' in reqs :
                show_systray = int(reqs['show_systray'][0])
                if show_systray != 0 and show_systray != 1:
                    success = False
                    data = '{"res":"fail, show_systray:%s"}' % show_systray        
            if success and 'auto_start' in reqs :
                auto_start = int(reqs['auto_start'][0])
                if auto_start != 0 and auto_start != 1:
                    success = False
                    data = '{"res":"fail, auto_start:%s"}' % auto_start
            if success and 'ossftp_address' in reqs:
                ossftp_address = reqs['ossftp_address'][0].strip()
                if not self.ip_check(ossftp_address):
                    success = False
                    data = '{"res":"fail, ilegal ossftp address: %s"}' % ossftp_address
 
            if success and 'ossftp_port' in reqs:
                ossftp_port = int(reqs['ossftp_port'][0])
                if ossftp_port < 0:
                    success = False
                    data = '{"res":"fail, ilegal ossftp port: %d"}' % ossftp_port
            if success and 'ossftp_loglevel' in reqs:
                ossftp_loglevel = reqs['ossftp_loglevel'][0].strip().upper()
                if (ossftp_loglevel not in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']):
                    success = False
                    data = '{"res":"fail, illegal ossftp log level: %s. Must be: DEBUG, INFO, WARNING, ERROR, CRITICAL"}' % ossftp_loglevel
            if success and 'ossftp_bucketendpoints' in reqs:
                ossftp_bucketendpoints = reqs['ossftp_bucketendpoints'][0].strip()
                
            if success:
                config.set(["modules", "launcher", "popup_webui"], popup_webui)
                config.set(["modules", "launcher", "show_systray"], show_systray)
                config.set(["modules", "launcher", "auto_start"], auto_start)
                config.set(["modules", "ossftp", "address"], ossftp_address)
                config.set(["modules", "ossftp", "port"], ossftp_port)
                config.set(["modules", "ossftp", "log_level"], ossftp_loglevel)
                config.set(["modules", "ossftp", "bucket_endpoints"], ossftp_bucketendpoints)
                config.save()
                if auto_start:
                    autorun.enable()
                else:
                    autorun.disable()
                data = '{"res":"success"}'
                launcher_log.info('Set config: %s', json.dumps(config.config, sort_keys=True, separators=(',',':'), indent=2))
            else:
                launcher_log.error(data)

        self.send_response('text/html', data)

    def req_log_handler(self):
        req = urlparse.urlparse(self.path).query
        reqs = urlparse.parse_qs(req, keep_blank_values=True)
        data = ''

        cmd = "get_last"
        if reqs["cmd"]:
            cmd = reqs["cmd"][0]
        
        if cmd == "get_new":
            last_no = int(reqs["last_no"][0])
            data = ossftp_log_tailer.get_lines(last_no)
        else:
            data = '{"res":"fail", "reason":"wrong cmd: %s"%cmd}'

        mimetype = 'text/plain'
        self.send_response(mimetype, data)
        
    def req_download_handler(self):
        req = urlparse.urlparse(self.path).query
        reqs = urlparse.parse_qs(req, keep_blank_values=True)
        data = ''

        if reqs['cmd'] == ['get_progress']:
            data = json.dumps(update_from_github.download_progress)

        self.send_response('text/html', data)

    def req_init_module_handler(self):
        req = urlparse.urlparse(self.path).query
        reqs = urlparse.parse_qs(req, keep_blank_values=True)
        data = ''

        try:
            module = reqs['module'][0]
            config.load()

            if reqs['cmd'] == ['start']:
                result = module_init.start(module)
                data = '{ "module": "%s", "cmd": "start", "result": "%s" }' % (module, result)
            elif reqs['cmd'] == ['stop']:
                result = module_init.stop(module)
                data = '{ "module": "%s", "cmd": "stop", "result": "%s" }' % (module, result)
            elif reqs['cmd'] == ['restart']:
                result_stop = module_init.stop(module)
                result_start = module_init.start(module)
                data = '{ "module": "%s", "cmd": "restart", "stop_result": "%s", "start_result": "%s" }' % (module, result_stop, result_start)
        except Exception as e:
            launcher_log.exception("init_module except:%s", e)

        self.send_response("text/html", data)

process = 0
server = 0
def start():
    global process, server
    server = LocalServer(("0.0.0.0", 8192), Http_Handler)
    process = threading.Thread(target=server.serve_forever)
    process.setDaemon(True)
    process.start()

def stop():
    global process, server
    if process == 0:
        return

    launcher_log.info("begin to exit web control")
    server.shutdown()
    server.server_close()
    process.join()
    launcher_log.info("launcher web control exited.")
    process = 0


def http_request(url, method="GET"):
    proxy_handler = urllib2.ProxyHandler({})
    opener = urllib2.build_opener(proxy_handler)
    try:
        req = opener.open(url, timeout=30)
        return req
    except Exception as e:
        #logging.exception("web_control http_request:%s fail:%s", url, e)
        return False

def confirm_ossftp_exit():
    launcher_log.debug("start confirm_ossftp_exit")
    for i in range(30):
        if http_request("http://127.0.0.1:8192/quit") == False:
            return True
        time.sleep(1)
    launcher_log.debug("finished confirm_ossftp_exit")
    return False

def confirm_module_ready(port):
    if port == 0:
        launcher_log.error("confirm_module_ready with port 0")
        time.sleep(1)
        return False

    for i in range(200):
        req = http_request("http://127.0.0.1:%d/is_ready" % port)
        if req == False:
            time.sleep(1)
            continue

        content = req.read(1024)
        req.close()
        #logging.debug("cert_import_ready return:%s", content)
        if content == "True":
            return True
        else:
            time.sleep(1)
    return False

if __name__ == "__main__":
    #confirm_ossftp_exit()
    http_request("http://getbootstrap.com/dist/js/bootstrap.min.js")
