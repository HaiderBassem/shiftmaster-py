from typing import Any, Generic, TypeVar
from pydantic import BaseModel

T = TypeVar("T")


class Meta(BaseModel):
    count: int | None = None


class ApiResponse(BaseModel, Generic[T]):
    success: bool = True
    data: T | None = None
    meta: Meta | None = None


class ErrorResponse(BaseModel):
    success: bool = False
    error: str


def ok(data: Any = None, count: int | None = None) -> dict:
    response = {"success": True, "data": data}
    if count is not None:
        response["meta"] = {"count": count}
    return response


def fail(message: str) -> dict:
    return {"success": False, "error": message}
