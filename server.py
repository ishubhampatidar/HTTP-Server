import socket
import sys
import traceback
from io import StringIO
from wsgiref.headers import Headers

class WSGIServer:
    def __init__(self, host='127.0.0.1', port=8000, app=None):
        self.host = host
        self.port = port
        self.app = app
        self.result = []

    def start_server(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as socket_server:
            socket_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            socket_server.bind((self.host, self.port))
            socket_server.listen(5)
            print(f"WSGI server running on http://{self.host}:{self.port}")

            while True:
                client_conn, client_add = socket_server.accept()
                with client_conn:
                    self.handle_request(client_conn)
    
    def http_response(self, status, response_headers, exc_info=None):
        headers = Headers(response_headers)
        self.result = [status, headers]
        return lambda data: None       
    
    def handle_request(self, client_conn):
        try:
            request_data = client_conn.recv(1024).decode('utf-8')
            if not request_data:
                return
            
            request_line = request_data.splitlines()[0]
            method, path, version = request_line.split()
            print(f"> {method} {path} {version}")

            # Build environ dictionary per WSGI spec
            environ = {
                'REQUEST_METHOD': method,
                'PATH_INFO': path,
                'SERVER_NAME': self.host,
                'SERVER_PORT': str(self.port),
                'wsgi.version': (1, 0),
                'wsgi.input': StringIO(''),
                'wsgi.errors': sys.stderr,
                'wsgi.multithread': False,
                'wsgi.multiprocess': False,
                'wsgi.run_once': False,
                'wsgi.url_scheme': 'http',
            }
         
            response_body = self.app(environ, self.http_response)
            status, headers = self.result

            #construct full HTTP response
            response_headers = ''.join(f"{k}: {v}\r\n" for k, v in headers.items())
            response = (
                f"HTTP/1.1 {status}\r\n"
                f"{response_headers}\r\n"
                f"{''.join([b.decode() if isinstance(b, bytes) else b for b in response_body])}"
            )
            
            client_conn.sendall(response.encode('utf-8'))

        except Exception as e:
            error_message = traceback.format_exc()
            print("Internal Server Error:\n", error_message)
            client_conn.sendall(b"HTTP/1.1 500 Internal Serve Error\r\nContent-Type: text\plain\r\n\r\nInternal Server Error")