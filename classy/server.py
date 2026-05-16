import asyncio
import ssl
from aiohttp import web

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

async def dispatcher(request: web.Request):

    method = request.method
    path = request.path

    for endpoint in endpoints:

        if endpoint["method"] == method and endpoint["path"] == path:

            handler = endpoint["handler"]

            try:

                if asyncio.iscoroutinefunction(handler):
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

    if 404 in error_handlers:
        return await error_handlers[404](request, None)

    return web.Response(
        text="404 Not Found",
        status=404
    )

async def start(
    host: str = "0.0.0.0",
    port: int = 8080,
    default_folder: str = ".",
    use_ssl: bool = False,
    certfile: str = "cert.pem",
    keyfile: str = "key.pem"
):

    app = web.Application()

    runner = web.AppRunner(app)

    await runner.setup()

    app.router.add_route(
        "*",
        "/api/{tail:.*}",
        dispatcher
    )

    app.router.add_static(
        "/",
        path=default_folder,
        show_index=True
    )

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

    print(f"Server started on {host}:{port}")

    while True:
        await asyncio.sleep(3600)

# if __name__ == "__main__":
#    asyncio.run(start())