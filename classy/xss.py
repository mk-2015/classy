import html
from functools import wraps
from aiohttp import web
from typing import Callable, Any

def sanitize_input(data: Any) -> Any:
    if isinstance(data, str):
        return html.escape(data, quote=True)
    
    elif isinstance(data, dict):
        return {key: sanitize_input(value) for key, value in data.items()}
    
    elif isinstance(data, list):
        return [sanitize_input(item) for item in data]
    
    return data


def preventv(trusted_websites: str = ""):
    def decorator(handler: Callable[[web.Request], Any]):
        @wraps(handler)
        async def wrapper(request: web.Request, *args, **kwargs):
            request["sanitized_data"] = {}
            
            if request.can_read_body and request.content_type == "application/json":
                try:
                    raw_json = await request.json()
                    request["sanitized_data"] = sanitize_input(raw_json)
                except Exception:
                    return web.Response(
                        text='{"error": "Malformed JSON payload"}',
                        status=400,
                        content_type="application/json"
                    )

            response = await handler(request, *args, **kwargs)
            
            csp_sources = f" 'self' {trusted_websites}".strip()
            response.headers["Content-Security-Policy"] = f"default-src {csp_sources}; object-src 'none';"
            response.headers["X-Content-Type-Options"] = "nosniff"
            response.headers["X-XSS-Protection"] = "0"
            response.headers["X-Frame-Options"] = "DENY"
            
            return response
            
        return wrapper
    return decorator