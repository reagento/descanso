from collections.abc import Awaitable, Callable
from typing import (
    Any,
    Concatenate,
    ParamSpec,
    Protocol,
    TypeVar,
    overload,
)

try:
    from typing import Unpack
except ImportError:
    T = TypeVar("T")
    Unpack = Any | T

from descanso.method_descriptor import MethodBinder
from descanso.request import RequestTransformer
from descanso.request_transformers import (
    Url,
)
from descanso.response import ResponseTransformer

DEFAULT_BODY_PARAM = "body"

_MethodResultT = TypeVar("_MethodResultT")
_MethodParamSpec = ParamSpec("_MethodParamSpec")


Transformer = RequestTransformer | ResponseTransformer
UrlSrc = str | Callable | Url


def url_transformer(url: UrlSrc) -> Url:
    if isinstance(url, Url):
        return url
    return Url(url)


class Decorator(Protocol):
    @overload
    def __call__(
        self,
        func: Callable[
            Concatenate[Any, _MethodParamSpec],
            Awaitable[_MethodResultT],
        ],
    ) -> MethodBinder[_MethodParamSpec, _MethodResultT]: ...

    @overload
    def __call__(
        self,
        func: Callable[Concatenate[Any, _MethodParamSpec], _MethodResultT],
    ) -> MethodBinder[_MethodParamSpec, _MethodResultT]: ...

    def __call__(self, *args, **kwargs):
        raise NotImplementedError
