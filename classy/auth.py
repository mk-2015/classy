import asyncio
import hashlib
import secrets
from functools import wraps
from typing import Callable, Any, Optional
from aiohttp import web
import aiohttp

def require_auth(
    validate_func: Callable[[web.Request], Any], 
    forbidden_function: Optional[Callable[..., Any]] = None
):
    def decorator(handler):
        @wraps(handler)
        async def wrapper(request: web.Request, *args, **kwargs):
            if asyncio.iscoroutinefunction(validate_func):
                is_valid = await validate_func(request)
            else:
                is_valid = validate_func(request)

            if is_valid:
                return await handler(request, *args, **kwargs)
            else:
                if forbidden_function is not None:
                    if asyncio.iscoroutinefunction(forbidden_function):
                        return await forbidden_function(request)
                    return forbidden_function(request)
                
                return web.Response(
                    text='{"error": "Forbidden: Invalid credentials"}',
                    status=403,
                    content_type="application/json"
                )       
        return wrapper
    return decorator


def shaVerify(token: str, stored_apikey_hash: str, salt: Optional[str] = None) -> bool:
    token_to_hash = (token + salt) if salt else token
    incoming_hash = hashlib.sha256(token_to_hash.encode('utf-8')).hexdigest()
    
    return secrets.compare_digest(
        incoming_hash.encode('utf-8'), 
        stored_apikey_hash.encode('utf-8')
    )