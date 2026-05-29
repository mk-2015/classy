import uuid
from typing import Any, Callable, Dict, List, Optional, Type
from classy.logger import log
from aiohttp import web

class Provider:
    def __init__(self, name: str, proc: List[Dict[str, bool]]):
        if getattr(self, "_initialized", False):
            raise PermissionError("Illegal Operation: Cannot re-initialize a running Provider.")

        self.name = name
        self.perms = {"disk": False, "network": False}
        self._initialized = True

        if not proc:
            log("Internal error: No ProcList can be Null or empty", level="ERROR")
            raise ValueError("ProcList cannot be Null or empty")
        
        self.proc = proc

        for proc_item in self.proc:
            if proc_item.get('disk'):
                self.perms['disk'] = True
            if proc_item.get('network'):
                self.perms['network'] = True

    async def __procrq__(self, request: web.Request) -> web.Request:
        log(f"[{self.name}] No process request dunder method initialized", level="DEBUG")
        return request

    async def __procrs__(self, response: web.Response) -> web.Response:
        log(f"[{self.name}] No process response dunder method initialized", level="DEBUG")
        return response

    def __getattribute__(self, name: str) -> Any:
        attr = object.__getattribute__(self, name)

        if callable(attr) and not name.startswith("_"):
            proc_func_name = f"__proc_{name}"
            
            try:
                proc_func: Callable[[], List[Dict[str, bool]]] = object.__getattribute__(self, proc_func_name)
                
                def secure_wrapper(*args, **kwargs):
                    requirements_list = proc_func()
                    
                    for req in requirements_list:
                        if req.get("requires_disk") and not self.perms["disk"]:
                            raise PermissionError(f"Access Denied: Missing 'disk' permission for {name}")
                            
                        if req.get("requires_network") and not self.perms["network"]:
                            raise PermissionError(f"Access Denied: Missing 'network' permission for {name}")

                    return attr(*args, **kwargs)

                return secure_wrapper

            except AttributeError:
                def strict_fallback_wrapper(*args, **kwargs):
                    raise PermissionError(f"Security Policy Violation: Every function must have a matching {proc_func_name}")
                return strict_fallback_wrapper

        return attr

_REGISTRY: Dict[str, Any] = {}

def extend(plugin_instance: Any, custom_id: Optional[str] = None, log: Optional[bool] = True) -> str:

    if not plugin_instance:
        raise ValueError("Invalid plugin instance.")

    plugin_id = custom_id or f"plug_{uuid.uuid4().hex[:12]}"
    
    _REGISTRY[plugin_id] = plugin_instance
    if log:
        log(f"Successfully loaded plugin: {getattr(plugin_instance, 'name', type(plugin_instance).__name__)} [{plugin_id}]", level="INFO")
    return plugin_id

def run(plugin_id: str) -> Any:
    if plugin_id not in _REGISTRY:
        raise KeyError(f"Plugin '{plugin_id}' is not registered.")
        
    return _REGISTRY[plugin_id]