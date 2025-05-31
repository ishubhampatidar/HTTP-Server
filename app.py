def sample_app(environ, http_response):
    path = environ.get('PATH_INFO', '/')
    try:
        if path == '/':
            response_body = 'Hello, WSGI Server!'
            status = '200 OK'
        elif path == '/error':
            raise ValueError("Manual error for testing")
        else:
            response_body = 'Not Found'
            status = '404 Not Found'

        response_heaers = [('Content-Type','text/plain')]
        http_response(status, response_heaers)
        return [response_body.encode('utf-8')]
    except Exception as e:
        status = '500 Internal Server Error'
        response_heaers = [('Content-Type','text\plain')]
        http_response(status, response_heaers)
        return [f"App Error: {str(e)}".encode('utf-8')]