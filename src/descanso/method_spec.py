from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Generic, ParamSpec, TypeVar

from .request import FieldIn, FieldOut, RequestTransformer
from .response import ResponseTransformer

_MethodResultT = TypeVar("_MethodResultT")
_MethodParamSpec = ParamSpec("_MethodParamSpec")


@dataclass
class MethodSpec(Generic[_MethodParamSpec, _MethodResultT]):
    name: str
    doc: str
    fields_in: list[FieldIn]
    fields_out: list[FieldOut]
    result_type: Any
    func: Callable[_MethodParamSpec, _MethodResultT]
    request_transformers: list[RequestTransformer]
    response_transformers: list[ResponseTransformer]
