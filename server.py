import socket
import sys
import os
import mimetypes
import traceback
from io import BytesIO
from wsgiref.headers import Headers
from urllib.parse import urlparse
from threading import Thread

class WSGIServer:
    def __init__(self, host='127.0.0.1', port=8000, app=None, static_dir='static', template_dir='templates'):
        self.host = host
        self.port = port
        self.app = app
        self.result = []
        self.static_dir = static_dir
        self.template_dir = template_dir

    def start_server(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as socket_server:
            socket_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            socket_server.bind((self.host, self.port))
            socket_server.listen(5)
            print(f"WSGI server running on http://{self.host}:{self.port}")

            while True:
                client_conn, client_add = socket_server.accept()
                thread = Thread(target=self.handle_request, args=(client_conn,))
                thread.start()
    
    def http_response(self, status, response_headers, exc_info=None):
        headers = Headers(response_headers)
        self.result = [status, headers]
        return lambda data: None

    def parse_headers(self, header_data):
        headers = {}
        lines = header_data.split('\r\n')[1:]   # skip request line
        for line in lines:
            key, sep, value = line.partition(': ')
            if sep:
                headers[key] = value
        return headers

    def serve_static_file(self, client_conn, path):
        try:
            file_path = os.path.join(self.static_dir, path[len('/static/'):])
            if not os.path.exists(file_path) or not os.path.isfile(file_path):
                self.send_404(client_conn)
                return
            
            with open(file_path, 'rb') as static_file:
                content  = static_file.read()

            content_type = mimetypes.guess_type(file_path)[0] or 'application\octet-stream'
            headers = f"HTTP/1.1 200 OK\r\nContent-Type: {content_type}\r\nContent-Lenght: {len(content)}\r\n\r\n"
            client_conn.sendall(headers.encode('utf-8') + content)
        except Exception as e:
            traceback.print_exc()
            self.send_500(client_conn)
    
    def send_404(self, client_conn):
        try:
            file_path = os.path.join(self.template_dir, '404.html')
            with open(file_path, 'rb') as f:
                content = f.read()
            
            headers = (
                "HTTP/1.1 404 Not Found\r\n"
                "Content-Type: text/html\r\n"
                f"Content-Length: {len(content)}\r\n\r\n"
            )

            client_conn.sendall(headers.encode('utf-8') + content)
        except Exception as e:
            traceback.print_exc()
            client_conn.sendall(b"HTTP/1.1 404 Not Found\r\nContent-Type: text/plain\r\n\r\n404 Not Found")

    def send_500(self, client_conn):
        client_conn.sendall(b"HTTP/1.1 500 Internal Server Error\r\nContent-Type: text/plain\r\n\r\nInternal Server Error")

    def handle_request(self, client_conn):
        try:
            request_data = b""
            while True:
                chunk = client_conn.recv(4096)
                request_data += chunk
                if len(chunk) < 4096:
                    break
            
            if not request_data:
                client_conn.close()
            
            request_text = request_data.decode('utf-8', errors='replace')
            request_line = request_text.split('\r\n')[0]
            method, full_path, http_version = request_line.split()
            # print(f"> {method} {path} {http_version}")

            # Separate headers and body
            header_data, _, body = request_text.partition('\r\n\r\n')
            headers = self.parse_headers(header_data)

            # Parse path and query string
            parsed_url = urlparse(full_path)
            path = parsed_url.path
            query_string = parsed_url.query

            # Serve the static file
            if path.startswith('/static'):
                self.serve_static_file(client_conn, path)
                return

            content_length = int(headers.get('content-length', 0))
            body_bytes = request_data.split(b'\r\n\r\n', 1)[1] if content_length else b""
            body_stream = BytesIO(body_bytes)

            # Build WSGI environ
            environ = {
                'REQUEST_METHOD': method,
                'PATH_INFO': path,
                'SERVER_NAME': self.host,
                'SERVER_PORT': str(self.port),
                'QUERY_STRING': query_string,
                'CONTENT_TYPE': headers.get('Content-Type', ''),
                'CONTENT_LENGTH': str(content_length),
                'wsgi.version': (1, 0),
                'wsgi.input': body_stream,
                'wsgi.errors': sys.stderr,
                'wsgi.multithread': True,
                'wsgi.multiprocess': False,
                'wsgi.run_once': False,
                'wsgi.url_scheme': 'http',
            }

            for key, value in headers.items():
                http_key = 'HTTP_' + key.upper().replace('-','_')
                if http_key not in ('HTTP_CONTENT_LENGTH','HTTP_CONTENT_TYPE'):
                    environ[http_key] = value
         
            response_body = self.app(environ, self.http_response)
            status, headers = self.result

            status_code = int(status.split()[0])
            if status_code == 404:
                self.send_404(client_conn)
                return

            #construct full HTTP response
            response_headers = ''.join(f"{k}: {v}\r\n" for k, v in headers.items())
            response = (
                f"HTTP/1.1 {status}\r\n"
                f"{response_headers}\r\n"
                f"{''.join([b.decode() if isinstance(b, bytes) else b for b in response_body])}"
            )
            
            client_conn.sendall(response.encode('utf-8'))

        except Exception as e:
            traceback.format_exc()
            client_conn.sendall(b"HTTP/1.1 500 Internal Serve Error\r\nContent-Type: text\plain\r\n\r\nInternal Server Error")
        
        finally:
            client_conn.close()