from server import WSGIServer
from app import sample_app

if __name__ == "__main__":
    server = WSGIServer(app=sample_app)
    server.start_server()