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


def shaVerify(token: str, apikey: str, salt: Optional[str] = None) -> bool:
    token_to_hash = (token + salt) if salt else token
    tokenhash = hashlib.sha256(token_to_hash.encode('utf-8')).hexdigest()
    
    return secrets.compare_digest(tokenhash, apikey)
    
def EItnAuth(client_token: str, server_token: str, server_salt: str) -> bool:
    server_token_to_hash = server_token + server_salt
    expected_hash = hashlib.sha256(server_token_to_hash.encode('utf-8')).hexdigest()
    
    return secrets.compare_digest(client_token, expected_hash)
    
async def AItnAuth(client_token: str, client_token_salt_url: str, client_token_at_first_contact: str) -> bool:
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(client_token_salt_url, timeout=3.0) as response:
                if response.status != 200:
                    return False
                remote_salt = await response.text()
                remote_salt = remote_salt.strip()
    except Exception:
        return False

    expected_source = client_token_at_first_contact + remote_salt
    expected_hash = hashlib.sha256(expected_source.encode('utf-8')).hexdigest()
    
    incoming_hash = hashlib.sha256(client_token.encode('utf-8')).hexdigest()
    
    return secrets.compare_digest(incoming_hash, expected_hash)