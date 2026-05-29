import inspect
import hashlib
import secrets
from functools import wraps
from typing import Callable, Any, Optional, Union, List
from aiohttp import web
from .logger import log

def require_auth(
    validate_func: Callable[[web.Request], Any],
    forbidden_function: Optional[Callable[..., Any]] = None
):
    def decorator(handler):
        @wraps(handler)
        async def wrapper(*args, **kwargs):
            request = kwargs.get('request')
            if not request:
                request = next((arg for arg in args if isinstance(arg, web.Request)), None)
            
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

def genNewToken(
    base32secret: str, 
    urienabled: Optional[bool] = False, 
    name: Optional[str] = "burger@pizza.net", 
    issuer: Optional[str] = "ILikeBurgersANDPizza.net"
) -> Optional[Union[str, List]]:
    try:
        import pyotp
        totp = pyotp.TOTP(base32secret)

        if urienabled:
            return totp.provisioning_uri(name=name, issuer_name=issuer)
        
        return totp.now()
    except ImportError:
        log("pyotp is not installed, please install the [betterauth] suite!", level="ERROR")
        return None
    except Exception as e:
        log(f"Encountered exception: {type(e).__name__}, Please check if base32secret is correct: {base32secret}", level="ERROR")
        return [e, type(e).__name__]
        

def verifytoken(base32secret: str, usersent: str) -> Optional[Union[bool, List]]:
    try:
        import pyotp
        totp = pyotp.TOTP(base32secret)
        return totp.verify(usersent)

    except ImportError:
        log("pyotp is not installed, please install the [betterauth] suite!", level="ERROR")
        return None
    except Exception as e:
        log(f"Encountered exception: {type(e).__name__}, Please check if totptoken secret is correct.", level="ERROR")
        return [e, type(e).__name__]