from collections.abc import Callable
from dataclasses import dataclass
from typing import TypeVar, ParamSpec, Generic, Any

from .request import RequestTransformer, Field
from .response import ResponseTransformer

_MethodResultT = TypeVar("_MethodResultT")
_MethodParamSpec = ParamSpec("_MethodParamSpec")


@dataclass
class MethodSpec(Generic[_MethodParamSpec, _MethodResultT]):
    name: str
    doc: str
    fields: list[Field]
    result_type: Any
    func: Callable[_MethodParamSpec, _MethodResultT]
    request_transformers: list[RequestTransformer]
    response_transformers: list[ResponseTransformer]
