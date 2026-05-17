from functools import wraps
from typing import Any, Dict, Type, get_type_hints
from aiohttp import web

class Schema:
    def __init__(self, data: Dict[str, Any]):
        hints = get_type_hints(self.__class__)
        self._errors = {}

        if not isinstance(data, dict):
            self._errors["_base"] = "Expected a structured object map."
            return

        for field_name, expected_type in hints.items():
            if field_name not in data:
                self._errors[field_name] = "This field is required."
                continue

            val = data[field_name]

            if isinstance(expected_type, type) and issubclass(expected_type, Schema):
                nested_instance = expected_type(val)
                if not nested_instance.is_valid:
                    self._errors[field_name] = nested_instance._errors
                else:
                    setattr(self, field_name, nested_instance)
                continue

            try:
                if expected_type is int:
                    val = int(val)
                elif expected_type is float:
                    val = float(val)
                elif expected_type is str:
                    val = str(val)
                elif expected_type is bool:
                    if isinstance(val, str):
                        val = val.lower() in ("true", "1", "yes", "y")
                    else:
                        val = bool(val)

                if not isinstance(val, expected_type):
                    raise ValueError()

                setattr(self, field_name, val)

            except (ValueError, TypeError):
                self._errors[field_name] = f"Must be valid type: '{expected_type.__name__}'."

    @property
    def is_valid(self) -> bool:
        return len(self._errors) == 0


def validate_schema(schema_class: Type[Schema]):
    def decorator(route_handler):
        @wraps(route_handler)
        async def wrapper(request: web.Request, *args, **kwargs):
            try:
                body = await request.json()
            except Exception:
                return web.json_response(
                    {"status": "error", "message": "Malformed or missing JSON payload."}, 
                    status=400
                )

            payload_instance = schema_class(body)

            if not payload_instance.is_valid:
                return web.json_response(
                    {"status": "error", "validation_failures": payload_instance._errors}, 
                    status=400
                )
            return await route_handler(request, payload=payload_instance, *args, **kwargs)

        return wrapper
    return decorator