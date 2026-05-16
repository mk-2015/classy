import ssl
from typing import Any, Dict, Tuple, Optional
from aiohttp import ClientSession, TCPConnector

_session_cache: Dict[Tuple[bool, Optional[str], Optional[str]], ClientSession] = {}
_connector_cache: Dict[Tuple[bool, Optional[str], Optional[str]], TCPConnector] = {}

async def get_session(
    use_ssl: bool, 
    keyfile: Optional[str], 
    certfile: Optional[str]
) -> ClientSession:
    global _session_cache, _connector_cache
    
    cache_key = (use_ssl, keyfile, certfile)
    session = _session_cache.get(cache_key)
    
    if session is None or session.closed:
        ssl_context = False
        if use_ssl:
            ssl_context = ssl.create_default_context()
            if keyfile and certfile:
                ssl_context.load_cert_chain(certfile=certfile, keyfile=keyfile)
        
        connector = TCPConnector(ssl=ssl_context, limit=100)
        session = ClientSession(connector=connector)
        
        _connector_cache[cache_key] = connector
        _session_cache[cache_key] = session
        
    return session

async def webresource(
    method: str, 
    url: str, 
    json_response: bool = False,
    headers: Optional[Dict[str, str]] = None, 
    payload: Any = None,
    use_ssl: bool = False, 
    keyfile: Optional[str] = "keyfile.pem", 
    certfile: Optional[str] = "certfile.pem"
) -> Tuple[int, Any]:
    request_headers = {k.lower(): v for k, v in (headers or {}).items()}
    session = await get_session(use_ssl, keyfile, certfile)

    kwargs: Dict[str, Any] = {}
    if payload is not None:
        raw_content_type = request_headers.get('content-type', '')
        content_type_parts = raw_content_type.split(';')
        media_type = content_type_parts[0].strip() if content_type_parts else ''
        is_json_content = (media_type == 'application/json')
        
        if isinstance(payload, dict) or is_json_content:
            kwargs['json'] = payload
            if 'content-type' not in request_headers:
                request_headers['content-type'] = 'application/json'
        else:
            kwargs['data'] = payload

    kwargs['headers'] = request_headers

    async with session.request(method=method.upper(), url=url, **kwargs) as response:
        if not json_response:
            return response.status, await response.text()
        return response.status, await response.json()

async def close_webresource_pool():
    global _session_cache, _connector_cache
    for session in _session_cache.values():
        if session and not session.closed:
            await session.close()
    for connector in _connector_cache.values():
        if connector and not connector.closed:
            await connector.close()
            
    _session_cache.clear()
    _connector_cache.clear()
