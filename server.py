import socket

class WSGIServer:
    def __init__(self, host='127.0.0.1', port=8000, app=None):
        self.host = host
        self.port = port
        self.app = app

    def start_server(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as socket_server:
            socket_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            socket_server.bind((self.host, self.port))
            socket_server.listen(5)
            print(f"WSGI server running on http://{self.host}:{self.port}")