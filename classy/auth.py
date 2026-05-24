import inspect
import hashlib
import secrets
from functools import wraps
from typing import Callable, Any, Optional
from aiohttp import web

def require_auth(
    validate_func: Callable[[web.Request], Any],
    forbidden_function: Optional[Callable[..., Any]] = None
):
    def decorator(handler):
        @wraps(handler)
        async def wrapper(*args, **kwargs):
            request = kwargs.get('request') or (args[1] if len(args) > 1 and isinstance(args[1], web.Request) else args[0])
            
            if inspect.iscoroutinefunction(validate_func):
                is_valid = await validate_func(request)
            else:
                is_valid = validate_func(request)

            if is_valid:
                return await handler(*args, **kwargs)
            
            if forbidden_function is not None:
                if inspect.iscoroutinefunction(forbidden_function):
                    return await forbidden_function(request)
                return forbidden_function(request)
            
            return web.json_response({"error": "Forbidden: Invalid credentials"}, status=403)       
        return wrapper
    return decorator


def shaVerify(token: str, stored_apikey_hash: str, salt: Optional[str] = None) -> bool:
    token_to_hash = (token + salt) if salt else token
    incoming_hash = hashlib.sha256(token_to_hash.encode('utf-8')).hexdigest()
    
    return secrets.compare_digest(
        incoming_hash.encode('utf-8'), 
        stored_apikey_hash.encode('utf-8')
    )

