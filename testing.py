from classy.server import endpoint_GET, endpoint_POST, start  
from classy.rate import rate_limit
from classy.schema import Schema, validate_schema
from aiohttp import web
import asyncio
from typing import Callable, Optional

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
    
class SignUp(Schema):
    Name: str
    Birth: str
    Age: Optional[int]
    Email: str
    
@endpoint_POST("/test/savemodel/{modelNo:int}/user/{user:str}")
@validate_schema(SignUp)
async def postage(request: web.Request, *args, **kwargs):
    modelNo = kwargs['modelNo']
    model = kwargs['body']
    user = kwargs['user']
    
    def thread_safe_file_write():
        with open("database.txt", "a+", encoding="utf-8") as file:
            file.seek(0)
            line = file.readline().strip()
            
            header = "database.txt:testing.py database example file"
            if line != header:
                file.seek(0, 0)
                file.write(header + "\n")
                
            file.seek(0, 2)
            file.write(f"USER={user}, MODELNO={modelNo}, model={model}\n")

    await asyncio.to_thread(thread_safe_file_write)

    return web.json_response({
        "success": True,
        "code": 201,
        "info": {
            "user": f"{user}",
            "modelNo": f"{modelNo}",
            "Message": f"user: {user}, created model: {modelNo}"
        }
    }, status=201)
        


asyncio.run(start(default_folder="."))