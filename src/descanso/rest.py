from typing import (
    TypeVar,
    Callable,
    ParamSpec,
)

from .method_descriptor import MethodBinder
from .request import RequestTransformer
from .response import ResponseTransformer
from .signature import make_method_spec

_MethodResultT = TypeVar("_MethodResultT")
_MethodParamSpec = ParamSpec("_MethodParamSpec")


def get(
    *transformers: RequestTransformer | ResponseTransformer,
) -> Callable[
    [Callable[_MethodParamSpec, _MethodResultT]],
    MethodBinder[_MethodParamSpec, _MethodResultT],
]:
    def inner(
        func: Callable[_MethodParamSpec, _MethodResultT],
    ) -> MethodBinder[_MethodParamSpec, _MethodResultT]:
        spec = make_method_spec(func, transformers=transformers)
        return MethodBinder(spec)

    return inner
