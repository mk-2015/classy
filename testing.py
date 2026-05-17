from classy.server import endpoint_GET, start
from classy.rate import rate_limit
from aiohttp import web
import asyncio

@endpoint_GET("/test")
async def test_endpoint(request):
    return web.Response(
        text="Hello!"
    )

@endpoint_GET("/test/prime/{prime:int}")
@rate_limit(50, 10)
async def test_prime(request: web.Request, prime: int):
    if prime < 2:
        return web.Response(
            text=f"{prime} is not prime."
        )

    for i in range(2, int(prime**0.5) + 1):
        if prime % i == 0:
            return web.Response(
                text=f"{prime} is not prime."
            )

    return web.Response(
        text=f"{prime} is prime!"
    )


asyncio.run(start(default_folder="."))