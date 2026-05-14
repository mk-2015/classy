import http.server
import ssl
import socketserver
import abc
import datetime
import classy.logger

endpoints = []
server = []

def endpoint_OPT(path):
    def decorator(func):
        func.http_method = 'OPTIONS'
        func.path = path
        endpoints.append(
            {
                "function": function,
                "http_method": 'OPTIONS',
                "path": path
            }
        )
        print(f"Registered GET endpoint: {path}")
    return function

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

def error_handler_add(intid, code):
    def decorator(func):
        func.error_id = intid
        func.error_code = code
        endpoints.append(
            {
                "spec": True,
                "code_handler": function,
                "http.error": code,
                "id-loc": 
                {
                    "integer-id": intid
                }
            }
        )
        print(f"Registered error hander for code: {code}")
    return function

class RequestException(Exception):
    def __init__(self, code, message):
        super().__init__(message)
        self.code = code
        self.message = message
        
       print(f"----------------------------")
       print(f" Ex: ServerExecption")
       print(f" Error: {code}")
       print(f" Message: {message} ")
       print(f"----------------------------")

class RequestHandler(http.server.BaseHTTPRequestHandler):
    def send_error(self, code, reason):
        for endpoint in endpoints:
            if endpoint['spec'] == True and endpoint['http.error'] == code:
                    endpoint['code_handler'](self, reason) 
            else:
                continue
        else:
            raise RequestException(-1, f"No error handler found for: {code} ")

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

    def do_OPTIONS(self):
        self.handle_request('OPTIONS')

    def handle_request(self, method):
        for endpoint in endpoints:
            if endpoint['http_method'] == method and endpoint['path'] == self.path:
                response = endpoint['function'](self)
                self.send_response(response['code'].int())
                self.end_headers()
                self.wfile.write(response['response'].encode())
                return
            
        self.send_response(404)
        self.end_headers()

def start(host: str = "", port: int = 8080, use_ssl: bool = False, keyfile: str = 'key.pem', certfile: str = 'cert.pem'):
    print("Starting server...")
    
    httpd = socketserver.ThreadingTCPServer((host, port), RequestHandler, bind_and_activate=False)

    try:
        if use_ssl:
            ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            ssl_context.load_cert_chain(certfile=certfile, keyfile=keyfile)
            httpd.socket = ssl_context.wrap_socket(httpd.socket, server_side=True)

        httpd.server_bind()
        httpd.server_activate()

        server.append({
            "server": httpd,
            "host": host,
            "port": port,
            "endpoints": endpoints
        })
        
        ssl_status = "Yes" if use_ssl else "No"
        print(f"Server started on {host or '0.0.0.0'}:{port}, SSL: {ssl_status}")
        
        httpd.serve_forever()

    except Exception as e:
        httpd.server_close()
        raise e