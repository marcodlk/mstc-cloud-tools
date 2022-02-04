import http.server
import os
from functools import partial
from http.server import SimpleHTTPRequestHandler

_roots = {}


class DataService:
    def __init__(self, root_dir, port=0, ip="0.0.0.0"):
        self.root_dir = os.path.abspath(str(root_dir))
        if not os.path.exists(self.root_dir):
            raise IOError(self.root_dir + " does not exist")
        self.port = port
        self.ip = ip
        self.server = None
        self.url = None

    def start(self):
        import socket
        import socketserver
        import threading

        socketserver.ThreadingTCPServer.allow_reuse_address = True
        handler = partial(_ServerHandler, directory=self.root_dir)
        self.server = socketserver.ThreadingTCPServer((self.ip, self.port), handler)
        ip, actual_port = self.server.server_address
        self.port = actual_port
        _roots[actual_port] = self.root_dir
        server_thread = threading.Thread(target=self.server.serve_forever)
        server_thread.name = "web server thread"
        server_thread.daemon = True
        server_thread.start()
        # host = socket.gethostbyname(socket.gethostname())
        host = socket.gethostname()
        self.url = "http://" + host + ":" + str(actual_port)
        return self.server, self.url

    def shutdown(self):
        self.server.shutdown()
        _roots.pop(self.port)


class _ServerHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        # Possible to wrap this and delete after get?
        return SimpleHTTPRequestHandler.do_GET(self)


if __name__ == "__main__":
    data_service = DataService(os.getcwd())
    s, serving = data_service.start()
    print("serving on " + serving)
    s.serve_forever()
