from collections.abc import Awaitable, Callable
from typing import (
    Any,
    Concatenate,
    Generic,
    ParamSpec,
    TypeVar,
    overload,
)

from .bound_method import BoundAsyncMethod, BoundSyncMethod
from .client import AsyncClient, SyncClient
from .method_spec import MethodSpec

_MethodResultT = TypeVar("_MethodResultT")
_MethodParamSpec = ParamSpec("_MethodParamSpec")


class MethodBinder(Generic[_MethodParamSpec, _MethodResultT]):
    def __init__(
        self,
        spec: MethodSpec[Concatenate[Any, _MethodParamSpec], _MethodResultT],
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
