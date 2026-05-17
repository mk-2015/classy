import asyncio
import os
import ssl
from sys import path
import colorama
import inspect
from aiohttp import request, request, web
from datetime import datetime

endpoints = []
error_handlers = {}

def route(method: str, path: str):
    def decorator(func):
        endpoints.append({
            "method": method.upper(),
            "path": path,
            "handler": func
        })

        print(f"Registered {method.upper()} endpoint: {path}")

        return func

    return decorator


def endpoint_GET(path):
    return route("GET", path)


def endpoint_POST(path):
    return route("POST", path)


def endpoint_PUT(path):
    return route("PUT", path)


def endpoint_DELETE(path):
    return route("DELETE", path)


def endpoint_PATCH(path):
    return route("PATCH", path)


def endpoint_OPTIONS(path):
    return route("OPTIONS", path)

def register_error(code: int):
    def decorator(func):
        error_handlers[code] = func

        print(f"Registered error handler for: {code}")

        return func

    return decorator


class RequestException(Exception):
    def __init__(self, code: int, message: str):
        self.code = code
        self.message = message
        super().__init__(message)

default_folder: str

async def dispatcher(request: web.Request):

    method = request.method
    path = request.path

    print(
        f"\n{datetime.now()} [{request.remote}] -- {path} {method}\n"
        f"Has sent headers: {dict(request.headers)}\n"
        f"Has sent query: {dict(request.query)}\n"
        f"Has sent cookies: {dict(request.cookies)}\n"
    )

    for endpoint in endpoints:

        if endpoint["method"] == method and endpoint["path"] == path:

            handler = endpoint["handler"]

            try:

                if inspect.iscoroutinefunction(handler):
                    result = await handler(request)
                else:
                    result = handler(request)

                if isinstance(result, web.Response):
                    return result

                if isinstance(result, dict):

                    return web.json_response(
                        result.get("response", {}),
                        status=result.get("code", 200)
                    )

                return web.Response(
                    text=str(result),
                    status=200
                )

            except RequestException as e:

                if e.code in error_handlers:
                    return await error_handlers[e.code](request, e)

                return web.Response(
                    text=e.message,
                    status=e.code
                )

            except Exception as e:
                print("Internal Error:", e)

                if 500 in error_handlers:
                    return await error_handlers[500](request, e)

                return web.Response(
                    text="500 Internal Server Error",
                    status=500
                )
            
    clean_path = path.lstrip("/")
    local_path = os.path.abspath(os.path.join(_default_folder, clean_path))
    base_dir = os.path.abspath(_default_folder)

    if not local_path.startswith(base_dir):
        if 404 in error_handlers:
            return await error_handlers[404](request, None)
        return web.Response(text="404 Not Found", status=404)

    if os.path.isdir(local_path):
        local_path = os.path.join(local_path, "index.html")

    if not os.path.exists(local_path) and not local_path.endswith(".html"):
        html_fallback = local_path + ".html"
        if os.path.exists(html_fallback):
            local_path = html_fallback

    if os.path.exists(local_path) and os.path.isfile(local_path):
        return web.FileResponse(local_path)

    requested_dir = os.path.abspath(os.path.join(_default_folder, path.lstrip("/")))
    
    if os.path.exists(requested_dir) and os.path.isdir(requested_dir):
        list_items = []
        try:
            for item in os.listdir(requested_dir):
                web_link_path = os.path.join(path, item).replace("\\", "/")
                list_items.append(f'<li><a href="{web_link_path}">{item}</a></li>')
                
            webtext = f"""
            <!DOCTYPE html>
            <html>
            <head><title>Directory listing for {path}</title></head>
            <body>
                <h1>Directory listing for {path}</h1>
                <hr>
                <ul>
                    {''.join(list_items)}
                </ul>
            </body>
            </html>
            """

            return web.Response(text=webtext, content_type="text/html", status=200)
            
        except Exception as e:
            print(f"Failed to generate directory listing: {e}")
            if 500 in error_handlers:
                return await error_handlers[500](request, e)

    if 404 in error_handlers:
        return await error_handlers[404](request, None)
        
    return web.Response(text="404 Not Found", status=404)

async def start(
    host: str = "0.0.0.0",
    port: int = 8080,
    default_folder: str = ".",
    use_ssl: bool = False,
    certfile: str = "cert.pem",
    keyfile: str = "key.pem"
):
    global _default_folder

    app = web.Application()

    _default_folder = default_folder

    app.router.add_route(
        "*",
        "/{tail:.*}",
        dispatcher
    )

    runner = web.AppRunner(app)
    await runner.setup()

    ssl_context = None

    if use_ssl:
        ssl_context = ssl.create_default_context(
            ssl.Purpose.CLIENT_AUTH
        )

        ssl_context.load_cert_chain(
            certfile=certfile,
            keyfile=keyfile
        )

    site = web.TCPSite(
        runner,
        host,
        port,
        ssl_context=ssl_context
    )

    await site.start()

    print(f"Server started on http{'s' if use_ssl else ''}://{host}:{port}")

    while True:
        await asyncio.sleep(3600)

# if __name__ == "__main__":
#    asyncio.run(start())