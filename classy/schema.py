from typing import Any, Dict, Optional, Type
from pydantic import BaseModel, ValidationError
from aiohttp import web
from functools import wraps

class Schema(BaseModel):
    model_config = {"extra": "forbid"}
    _errors: Dict[str, Any] = {}

    @classmethod
    def validate_data(cls, data: Dict[str, Any]) -> "Schema":
        instance = cls.model_construct()
        object.__setattr__(instance, "_errors", {})

        if not isinstance(data, dict):
            instance._errors["_base"] = "Expected a structured object map."
            return instance

        try:
            validated_instance = cls.model_validate(data)
            instance.__dict__.update(validated_instance.__dict__)
        except ValidationError as exc:
            for error in exc.errors(include_url=False):
                field_name = str(error["loc"][0]) if error["loc"] else "_base"
                instance._errors[field_name] = error["msg"]
        except Exception as exc:
            instance._errors["_base"] = f"Unexpected processing crash: {str(exc)}"

        return instance

    @property
    def is_valid(self) -> bool:
        return len(self._errors) == 0

    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in self.__dict__.items() if not k.startswith("_")}


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

            payload_instance = schema_class.validate_data(body_data)

            if not payload_instance.is_valid:
                return web.json_response(
                    {"status": "error", "validation_failures": payload_instance._errors},
                    status=400
                )

            kwargs['body'] = payload_instance
            return await route_handler(request, *args, **kwargs)

        return wrapper
    return decorator
