import http.server
import ssl
import socketserver
import abc
import datetime
import classy.logger

endpoints = []
server = []

def endpoint_GET(path):
    def decorator(func):
        func.http_method = 'GET'
        func.path = path
        endpoints.append(
            {
                "function": function,
                "http_method": 'GET',
                "path": path
            }
        )
        print(f"Registered GET endpoint: {path}")
    return function

def endpoint_POST(path):
    def decorator(func):
        func.http_method = 'POST'
        func.path = path
        endpoints.append(
            {
                "function": function,
                "http_method": 'POST',
                "path": path
            }
        )
    print(f"Registered POST endpoint: {path}")
    return function

def endpoint_PUT(path):
    def decorator(func):
        func.http_method = 'PUT'
        func.path = path
        endpoints.append(
            {
                "function": function,
                "http_method": 'PUT',
                "path": path
            }
        )
        print(f"Registered PUT endpoint: {path}")
    return function

def endpoint_DELETE(path):
    def decorator(func):
        func.http_method = 'DELETE'
        func.path = path
        endpoints.append(
            {
                "function": function,
            "http_method": 'DELETE',
            "path": path
        }
    )
    print(f"Registered DELETE endpoint: {path}")
    return function

def endpoint_PATCH(path):
    def decorator(func):
        func.http_method = 'PATCH'
        func.path = path
        endpoints.append(
            {
                "function": function,
                "http_method": 'PATCH',
                "path": path
            }
        )
        print(f"Registered PATCH endpoint: {path}")
    return function

class RequestHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.handle_request('GET')

    def do_POST(self):
        self.handle_request('POST')

    def do_PUT(self):
        self.handle_request('PUT')

    def do_DELETE(self):
        self.handle_request('DELETE')

    def do_PATCH(self):
        self.handle_request('PATCH')

    def handle_request(self, method):
        for endpoint in endpoints:
            if endpoint['http_method'] == method and endpoint['path'] == self.path:
                response = endpoint['function'](self)
                self.send_response(200)
                self.end_headers()
                self.wfile.write(response.encode())
                return
            
        self.send_response(404)
        self.end_headers()
        self.wfile.write(b'Endpoint not found')

def start(host="", port=8080, use_ssl=False, keyfile='key.pem', certfile='cert.pem'):
    print("Starting server...")
    with socketserver.TCPServer((host, port), RequestHandler) as httpd:

        if use_ssl:
            ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            ssl_context.load_cert_chain(certfile=certfile, keyfile=keyfile)
            httpd.socket = ssl_context.wrap_socket(httpd.socket, server_side=True)

        server.append(
            {
                "server": httpd,
                "host": host,
                "port": port,
                "endpoints": endpoints
            }
        )
        print(f"Server started on {host}:{port}, SSL: {use_ssl and 'Yes' or 'No'}")
        httpd.serve_forever()
