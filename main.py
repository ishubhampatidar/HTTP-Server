from server import WSGIServer
from app import sample_app
from flask_app import app as flask_app

if __name__ == "__main__":
    server = WSGIServer(app=flask_app)
    server.start_server()