import time
from functools import wraps
from typing import Dict, Tuple, Optional
from aiohttp import web

_rate_limit_cache: Dict[str, Tuple[float, float]] = {}

def rate_limit(max_tokens: int, refill_period_seconds: int, minus_token_amount: float = 1.0):
    refill_rate_per_second = max_tokens / refill_period_seconds

    def decorator(handler):
        @wraps(handler)
        async def wrapper(request: web.Request, *args, **kwargs):
            global _rate_limit_cache
            
            client_ip = request.remote
            current_time = time.time()
            if client_ip not in _rate_limit_cache:
                tokens = float(max_tokens)
            else:
                old_tokens, last_check = _rate_limit_cache[client_ip]
                
                elapsed_time = current_time - last_check
                tokens = min(float(max_tokens), old_tokens + (elapsed_time * refill_rate_per_second))

            if tokens >= minus_token_amount:
                tokens -= minus_token_amount
                _rate_limit_cache[client_ip] = (tokens, current_time)
                return await handler(request, *args, **kwargs)

            _rate_limit_cache[client_ip] = (tokens, current_time)

            retry_after = int((minus_token_amount - tokens) / refill_rate_per_second) or 1
            
            return web.Response(
                text=f'{{"error": "Too Many Requests", "retry_after_seconds": {retry_after}}}',
                status=429,
                content_type="application/json",
                headers={"Retry-After": str(retry_after)}
            )
            
        return wrapper
    return decorator