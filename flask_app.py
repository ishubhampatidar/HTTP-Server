from flask import Flask, request

app = Flask(__name__)

@app.route('/')
def hello():
    return 'Hello from Flask on custom WSGI server!'

@app.route('/greet/<name>')
def greet(name):
    return f'Hello, {name}!'

@app.route('/echo', methods=['POST'])
def echo():
    return f"Posted: {request.data.decode('utf-8')}"