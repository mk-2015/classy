import re
from functools import wraps
from typing import Callable, Dict, Any, Optional, Tuple
from aiohttp import web

PARAM_REGEX = re.compile(r"\{([a-zA-Z_][a-zA-Z0-9_]*)(?::([a-zA-Z_][a-zA-Z0-9_]*))?\}")

TYPE_MAPPING = {
    "int": (r"\d+", int),
    "str": (r"[^/]+", str),
    "uuid": (r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}", str),
    "path": (r".+", str)
}

def compile_route_path(route_template: str) -> Tuple[re.Pattern, Dict[str, Callable]]:
    regex_parts = []
    type_casters = {}
    last_pos = 0

    for match in PARAM_REGEX.finditer(route_template):
        regex_parts.append(re.escape(route_template[last_pos:match.start()]))
        
        param_name = match.group(1)
        type_name = match.group(2) or "str"

        if type_name not in TYPE_MAPPING:
            raise ValueError(f"Unsupported path type parameter mapping: '{type_name}'")

        pattern, caster = TYPE_MAPPING[type_name]
        
        regex_parts.append(f"(?P<{param_name}>{pattern})")
        type_casters[param_name] = caster
        
        last_pos = match.end()

    regex_parts.append(re.escape(route_template[last_pos:]))
    
    compiled_regex = re.compile(f"^{''.join(regex_parts)}$")
    return compiled_regex, type_casters