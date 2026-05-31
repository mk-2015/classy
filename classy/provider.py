import uuid
from typing import Any, Callable, Dict, List, Optional, Type, Union
from classy.logger import log
from aiohttp import web
from abc import ABC, abstractmethod
import inspect
import asyncio

class Provider(ABC):
    def __init__(self, name: str, proc: List[Dict[str, bool]], Private: bool = False):
        if getattr(self, "_initialized", False):
            raise PermissionError("Illegal Operation: Cannot re-initialize a running Provider.")

        forbidden_chars = {" ", "<", ">", "/", "\\","[", "]"}
        
        if any(char in name for char in forbidden_chars):
            raise ValueError(
                f"Invalid provider name '{name}': Names cannot contain spaces, "
                f"slashes, brackets, angle brackets, colons, or '@' symbols."
            )
        
        self.name = name
        self.perms = {"disk": False, "network": False, "messaging": False}
        self.private = Private
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
            if proc_item.get('messaging'):
                self.perms['messaging'] = True

    async def __procrq__(self, request: web.Request) -> web.Request:
        log(f"[{self.name}] No process request dunder method initialized", level="DEBUG")
        return request

    async def __procrs__(self, response: web.Response) -> web.Response:
        log(f"[{self.name}] No process response dunder method initialized", level="DEBUG")
        return response

    def __getattribute__(self, name: str) -> Any:
        attrib = object.__getattribute__(self, name)

        if callable(attrib) and not name.startswith("_"):
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

                        if req.get("requires_messaging") and not self.perms["messaging"]:
                            raise PermissionError(f"Access Denied: Missing 'messaging' permission for {name}")

                    ret = attrib(*args, **kwargs)
                    
                    if inspect.iscoroutine(ret):
                        async def async_delegate():
                            return await ret
                        return async_delegate()
                    
                    return ret
                return secure_wrapper

            except AttributeError:
                def strict_fallback_wrapper(*args, **kwargs):
                    raise PermissionError(f"Security Policy Violation: Every function must have a matching {proc_func_name}")
                return strict_fallback_wrapper

        return attrib

    @abstractmethod
    async def __boot(self, name):
        return {"errors": "Not implemented"}

    async def __boot_(self) -> dict:
        print(f"Booting provider: {self.name}")
        ret = await self.__boot(self.name)
        
        if type(ret) != dict:
            return {"error": "Invalid error datatype"}
        
        return ret.get("errors", ret)

    # Not required
    async def __when_recive_message(self, provider: str, message: dict):
        return {"error":"Not implemented"}


_REGISTRY: Dict[str, Any] = {}
_CENTRAL_BUS_QUEUES: Dict[str, asyncio.Queue] = {}
QUEUE_MAX_SIZE = 100

async def __send_message(caller: Provider, provider: str, message: dict) -> dict:
    if caller.perms.get("messaging") != True:
        raise PermissionError("Access Denied: Caller does not have 'messaging' permission.")
    
    if provider not in _REGISTRY:
        return {"error": f"Provider '{provider}' not found."}
    
    target_provider = _REGISTRY[provider]
    
    target_queue = _CENTRAL_BUS_QUEUES.get(provider)
    if not target_queue:
        return {"error": f"Internal error: No message queue found for provider '{provider}'."}

    try:
        target_queue.put_nowait({
            "sender": caller.name,
            "payload": message
        })
        return {"status": "accepted into tenant buffer"}
    
    except asyncio.QueueFull:
        log(f"Channel Backpressure: Mailbox for '{provider}' is fully saturated. Check if the plugin provider is a malicious plugin", level="WARNING")
        return {"error": f"Resource Exhaustion: Target mailbox queue is full."}
    

async def __list_providers(the_person_who_called: Provider) -> List[str]:
    listnames = []

    for plugin_id, instance in _REGISTRY.items():
        if instance.private and instance.private != the_person_who_called.private:
            listnames.append("<REDACTED>")
        else:
            listnames.append(getattr(instance, "name", plugin_id))

    return listnames

JANITOR_STARTED = False

async def extend(plugin_instance: Any, custom_id: Optional[str] = None, logged: Optional[bool] = True) -> str:
    if not plugin_instance:
        raise ValueError("Invalid plugin instance.")

    plugin_id = custom_id or f"plug_{uuid.uuid4().hex[:12]}"
    _REGISTRY[plugin_id] = plugin_instance
    _CENTRAL_BUS_QUEUES[plugin_id] = asyncio.Queue(maxsize=QUEUE_MAX_SIZE)
    
    if not JANITOR_STARTED:
        asyncio.create_task(start_queue_janitor(), name="ClassyQueueJanitor")
        JANITOR_STARTED = True

    boot_status = await _REGISTRY[plugin_id].__boot_()
    
    if boot_status in [{"errors": "Not implemented"}, {"error": "Invalid error datatype"}]:
        raise RuntimeError("Cannot boot Provider. If you are the developer of this Provider check the __boot function")
        
    if logged:
        log(f"Successfully loaded plugin: {getattr(plugin_instance, 'name', type(plugin_instance).__name__)} [{plugin_id}]", level="INFO")
    return plugin_id


def run(plugin_id: str) -> Any:
    if plugin_id not in _REGISTRY:
        raise KeyError(f"Plugin '{plugin_id}' is not registered.")
        
    return _REGISTRY[plugin_id]


async def start_queue_janitor():
    while True:
        await asyncio.sleep(10)
        
        for provider_id, queue in _CENTRAL_BUS_QUEUES.items():
            if queue.empty():
                continue
                
            dropped_count = 0
            
            for _ in range(50):
                try:
                    queue.get_nowait()
                    queue.task_done()
                    dropped_count += 1
                except asyncio.QueueEmpty:
                    break
