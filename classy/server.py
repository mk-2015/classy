import asyncio
import os
import ssl
import time
import traceback
from collections.abc import Callable
from datetime import datetime
from typing import Any, Dict, List
import colorama
from aiohttp import web
from ._server_helper import compile_route_path

endpoints: List[Dict[str, Any]] = []
error_handlers: Dict[int, Callable[..., Any]] = {}
middleware: List[Callable[..., Any]] = []

def route(method: str, path_template: str):
    compiled_pattern, type_casters = compile_route_path(path_template)

    def decorator(func: Callable):
        endpoints.append({
            "method": method.upper(),
            "path_template": path_template,
            "compiled_pattern": compiled_pattern,
            "type_casters": type_casters,
            "handler": func
        })

        print(f"Registered {method.upper()} endpoint: {path_template}")
        return func
    return decorator


def endpoint_GET(path): return route("GET", path)
def endpoint_POST(path): return route("POST", path)
def endpoint_PUT(path): return route("PUT", path)
def endpoint_PATCH(path): return route("PATCH", path)
def endpoint_DELETE(path): return route("DELETE", path)
def endpoint_HEAD(path): return route("HEAD", path)
def endpoint_OPTIONS(path): return route("OPTIONS", path)

def register_error(code: int):
    def decorator(func):
        if code in error_handlers:
            raise RuntimeError(
                f"Error handle for {code} is already registered"
            )
            
        error_handlers[code] = func

        print(f"Registered error handler for: {code}")

        return func

    return decorator

def use(middleware_func: Callable):
    if not callable(middleware_func):
        raise TypeError("Input is not a Callable type or object")
        
    middleware.append(middleware_func)

class RequestException(Exception):
    def __init__(self, code: int, message: str):
        self.code = code
        self.message = message
        super().__init__(message)

default_folder: str

async def _handler(request: web.Request, e: Exception) -> web.Response:
    tb_summary = traceback.extract_tb(e.__traceback__)
    filename, line, func, text = tb_summary[-1] if tb_summary else ("Unknown", 0, "Unknown", "Unknown")

    print(f"\n{colorama.Fore.RED}{colorama.Style.BRIGHT}×  An error occurred whilst processing request")
    print(f"{colorama.Fore.RED}├── Exception: {colorama.Fore.WHITE}{type(e).__name__}: {e}")
    print(f"{colorama.Fore.RED}└── Location:  {colorama.Fore.CYAN}{filename}:{line} in {func}() -> '{text}'")

    if isinstance(e, RequestException):
        return web.Response(text=e.message, status=e.code)

    if 500 in error_handlers:
        return await error_handlers[500](request, e)
    
    return web.Response(
        text="500 Internal Server Error",
        status=500
    )

async def execute_pipeline(request: web.Request, route_handler: Callable, *args, **kwargs):
    
    async def dispatch(idx: int):
        if idx < len(middleware):
            current_middleware = middleware[idx]
            async def next_layer():
                return await dispatch(idx + 1)
            return await current_middleware(request, next_layer, *args, **kwargs)
        else:
            return await route_handler(request, *args, **kwargs)

    return await dispatch(0)

async def dispatcher(request: web.Request):
    try:
        method = request.method
        path = request.path

        print(
            f"\n{datetime.now()} [{request.remote}] -- {path} {method}\n"
            f"Has sent headers: {dict(request.headers)}\n"
            f"Has sent query: {dict(request.query)}\n"
            f"Has sent cookies: {dict(request.cookies)}\n"
        )

        for endpoint in endpoints:
            if endpoint["method"] == method:
                match = endpoint["compiled_pattern"].match(path)
                
                if match:
                    handler = endpoint["handler"]
                    raw_params = match.groupdict()
                    casted_kwargs = {}
                    
                    try:
                        for param_name, raw_string_val in raw_params.items():
                            caster_func = endpoint["type_casters"][param_name]
                            casted_kwargs[param_name] = caster_func(raw_string_val)
                    except (ValueError, TypeError):
                        return web.json_response(
                            {"error": "Invalid URL path parameter type format alignment"}, 
                            status=400
                        )

                    args = ()
                    kwargs = casted_kwargs

                    try:
                        result = await execute_pipeline(request, handler, *args, **kwargs)
                    except RequestException as exc:
                        if exc.code in error_handlers:
                            return await error_handlers[exc.code](request, exc)
                        return web.Response(text=exc.message, status=exc.code)
                    except Exception as exc:
                        if 500 in error_handlers:
                            return await error_handlers[500](request, exc)
                        return web.Response(text="500 Internal Server Error", status=500)

                    if isinstance(result, web.Response):
                        return result

                    if isinstance(result, dict):
                        return web.json_response(result.get("response", {}), status=result.get("code", 200))

                    return web.Response(text=str(result), status=200)
                    
        # Boilerplate so user dosent get back an empty page(s)
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
    except Exception as e:
        return await _handler(request, e)

async def start(
    host: str = "0.0.0.0",
    port: int = 8080,
    default_folder: str = ".",
    use_ssl: bool = False,
    certfile: str = "cert.pem",
    keyfile: str = "key.pem"
):
    global _default_folder

    async def ratelimit_cleanup_task():
        from . import rate
        while True:
            await asyncio.sleep(60)
            now = time.time()
            cache = rate._rate_limit_cache
            to_delete = [ip for ip, (_, last_check) in cache.items() if now - last_check > 3600]
            
            for ip in to_delete:
                try:
                    del cache[ip]
                except KeyError:
                    pass

    asyncio.create_task(ratelimit_cleanup_task(), name="ClassyRateLimitGarbageCollector")

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