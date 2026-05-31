from typing import Optional
from classy.provider import Provider

class MemoryCache(Provider):
    def __init__(self):
        super().__init__("MemoryCache-ServiceProvider", [{"disk": False, "network": False}])
        self.cache = {}

    def __proc_cache_set(self):
        return [{"requires_disk": False}]

    def cache_set(self, key: str, value: str):
        self.cache[key] = value
        return f"Set {key} to {value} in cache."

    def __proc_cache_get(self):
        return [{"requires_disk": False}]

    def cache_get(self, key: str) -> Optional[str]:
        return self.cache.get(key, None)

    def __proc_cache_clear(self):
        return [{"requires_disk": False}]
    
    def cache_clear(self):
        self.cache.clear()
        return "Cache cleared."
    
    def __proc_cache_remove(self): 
        return [{"requires_disk": False}]

    def cache_remove(self, key: str):
        if key in self.cache:
            del self.cache[key]
            return f"Removed {key} from cache."
        return f"{key} not found in cache."