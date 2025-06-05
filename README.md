# 🌀 Custom WSGI Web Server in Python

A lightweight, WSGI-compliant web server built from scratch using raw Python sockets. This server is capable of running any Python web application that conforms to the [WSGI specification](https://www.python.org/dev/peps/pep-0333/), including Flask. It supports static file serving, multithreaded request handling, access logging, and customizable error pages — all without relying on external libraries or frameworks.

---

## 🚀 Features

- ✅ **WSGI-Compliant**  
  Fully supports WSGI-based apps like Flask, making it plug-and-play for real-world web applications.

- 🧵 **Multithreaded Request Handling**  
  Handles multiple simultaneous client connections using Python’s built-in `threading` module.

- 📂 **Static File Serving**  
  Automatically serves files from a `/static/` directory with correct MIME types and HTTP headers.

- 🧾 **Custom 404 Error Pages**  
  Uses a templated `404.html` page to handle invalid routes and missing static assets gracefully.

- 📊 **Access Logging**  
  Logs all incoming HTTP requests with timestamp, IP address, method, path, and status code.

- ⚙️ **Raw Socket Programming**  
  Built from the ground up using Python’s `socket` module and manual HTTP parsing.

---


🧠 How It Works
- The server listens on a raw TCP socket using Python's socket module.
- Each incoming request is parsed for method, path, headers, and body.
- If the path points to a static file, it is served directly.
- Otherwise, the request is wrapped in a WSGI environ and passed to the mounted WSGI app (like Flask).
- Custom 404 handling is triggered for both static and dynamic paths when not found.
- Access logs are printed for every request.
