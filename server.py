import socket
import sys
import traceback
from io import BytesIO
from wsgiref.headers import Headers
from urllib.parse import urlparse

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
                self.handle_request(client_conn)
    
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
                'wsgi.multithread': False,
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
            # print("Internal Server Error:\n", error_message)
            client_conn.sendall(b"HTTP/1.1 500 Internal Serve Error\r\nContent-Type: text\plain\r\n\r\nInternal Server Error")
        
        finally:
            client_conn.close()