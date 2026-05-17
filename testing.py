from classy.server import endpoint_GET, start
from aiohttp import web
import asyncio

@endpoint_GET("/test")
def test_endpoint(request):
    return web.Response(
        text="Hello!"
    )

asyncio.run(start(default_folder="."))