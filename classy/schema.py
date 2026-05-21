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
                        lowered = val.lower()
                        if lowered in ("true", "1", "yes", "y"):
                            val = True
                        elif lowered in ("false", "0", "no", "n"):
                            val = False
                        else:
                            raise ValueError("Value is neither Truthy nor Falsy")
                    else:
                        val = bool(val)

                if not isinstance(val, expected_type):
                    raise ValueError()

                setattr(self, field_name, val)

            except (ValueError, TypeError):
                self._errors[field_name] = f"Must be valid type: '{expected_type.__name__}'."

    @property
    def is_valid(self) -> bool:
        if len(self._errors) > 0:
            return False
        
        # Recursively check nested schemas
        hints = get_type_hints(self.__class__)
        for field_name in hints:
            if hasattr(self, field_name):
                val = getattr(self, field_name)
                if isinstance(val, Schema) and not val.is_valid:
                    return False
        
        return True
        
    @classmethod
    def get_field_type(cls, field_name: str) -> Any:
        hints = get_type_hints(cls)
        return hints.get(field_name)

    def get_value(self, field_name: str, default: Any = None) -> Any:
        return getattr(self, field_name, default)
        
    def __getitem__(self, item: str) -> Any:
        if hasattr(self, item):
            return getattr(self, item)
        raise KeyError(f"Field '{item}' does not exist or schema is invalid.")

    def to_dict(self) -> Dict[str, Any]:
        hints = get_type_hints(self.__class__)
        result = {}
        for field in hints:
            if hasattr(self, field):
                val = getattr(self, field)
                if isinstance(val, Schema) and hasattr(val, 'to_dict'):
                    result[field] = val.to_dict()
                else:
                    result[field] = val
        return result

def validate_schema(schema_class: Type[Schema]):
    def decorator(route_handler):
        @wraps(route_handler)
        async def wrapper(request: web.Request, *args, **kwargs):
            try:
                body_data = await request.json()
            except Exception:
                return web.json_response(
                    {"status": "error", "message": "Malformed or missing JSON payload."}, 
                    status=400
                )

            payload_instance = schema_class(body_data)

            if not payload_instance.is_valid:
                return web.json_response(
                    {"status": "error", "validation_failures": payload_instance._errors}, 
                    status=400
                )

            kwargs['body'] = payload_instance
            return await route_handler(request, *args, **kwargs)

        return wrapper
    return decorator
