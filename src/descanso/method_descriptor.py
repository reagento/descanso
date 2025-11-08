from collections.abc import Awaitable, Callable
from inspect import getcallargs
from typing import (
    Any,
    Generic,
    ParamSpec,
    TypeVar,
    overload,
)

from .client import AsyncClient, SyncClient
from .methodspec import MethodSpec
from .request import HttpRequest
from .response import HttpResponse


def make_request(spec: MethodSpec, args: dict[str, Any]) -> HttpRequest:
    request = HttpRequest()
    for transformer in spec.request_transformers:
        transformer.transform_request(request, args)
    return request


def make_response(
    spec: MethodSpec,
    response: HttpResponse,
    args: dict[str, Any],
) -> Any:
    for transformer in spec.response_transformers:
        response = transformer.transform_response(response, args)
    return response.body


def need_response_body(
    spec: MethodSpec,
    response: HttpResponse,
) -> bool:
    for transformer in spec.response_transformers:
        if transformer.need_response_body(response):
            return True
    return False


class BoundSyncMethod:
    def __init__(self, spec: MethodSpec, client: SyncClient) -> None:
        self._spec = spec
        self._client = client

    def __call__(self, *args, **kwargs):
        args = getcallargs(self._spec.func, self._client, *args, **kwargs)
        request = make_request(self._spec, args)
        with self._client.send_request(request) as response:
            if need_response_body(self._spec, response):
                response.load_body()
        return make_response(self._spec, response, args)


class BoundAsyncMethod:
    def __init__(self, spec: MethodSpec, client: AsyncClient) -> None:
        self._spec = spec
        self._client = client

    async def __call__(self, *args, **kwargs):
        args = getcallargs(self._spec.func, self._client, *args, **kwargs)
        request = make_request(self._spec, args)
        async with self._client.asend_request(request) as response:
            if need_response_body(self._spec, response):
                await response.aload_body()
        return make_response(self._spec, response, args)


_MethodResultT = TypeVar("_MethodResultT")
_MethodParamSpec = ParamSpec("_MethodParamSpec")


class MethodBinder(Generic[_MethodParamSpec, _MethodResultT]):
    def __init__(
        self,
        spec: MethodSpec[_MethodParamSpec, _MethodResultT],
    ) -> None:
        self._spec = spec

    @overload
    def __get__(
        self,
        instance: SyncClient,
        owner: Any = None,
    ) -> Callable[_MethodParamSpec, _MethodResultT]: ...

    @overload
    def __get__(
        self,
        instance: AsyncClient,
        owner: Any = None,
    ) -> Callable[_MethodParamSpec, Awaitable[_MethodResultT]]: ...

    @overload
    def __get__(
        self,
        instance: None,
        owner: Any = None,
    ) -> MethodSpec[_MethodParamSpec, _MethodResultT]: ...

    def __get__(
        self,
        instance: Any,
        owner: Any = None,
    ) -> Any:
        if instance is None:
            return self._spec
        elif isinstance(instance, SyncClient):
            return BoundSyncMethod(self._spec, instance)
        elif isinstance(instance, AsyncClient):
            return BoundAsyncMethod(self._spec, instance)
        else:
            raise TypeError
