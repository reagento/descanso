from typing import (
    TypeVar,
    Callable,
    Any,
    ParamSpec,
    Generic,
    overload,
    Awaitable,
    Protocol,
    reveal_type,
)


from .apply import SyncClient, AsyncClient, apply_sync, apply_async
from .methodspec import MethodSpec
from .request import RequestTransformer
from .response import ResponseTransformer
from .signature import make_method_spec


class BoundSyncMethod:
    def __init__(self, spec: MethodSpec, client: SyncClient) -> None:
        self._spec = spec
        self._client = client

    def __call__(self, *args, **kwargs):
        return apply_sync(
            client=self._client,
            spec=self._spec,
            args=args,
            kwargs=kwargs,
        )


class BoundAsyncMethod:
    def __init__(self, spec: MethodSpec, client: AsyncClient) -> None:
        self._spec = spec
        self._client = client

    def __call__(self, *args, **kwargs):
        return apply_async(
            client=self._client,
            spec=self._spec,
            args=args,
            kwargs=kwargs,
        )


_MethodResultT = TypeVar("_MethodResultT")
_MethodParamSpec = ParamSpec("_MethodParamSpec")


class MethodBinder(Generic[_MethodParamSpec, _MethodResultT]):
    def __init__(
        self, spec: MethodSpec[_MethodParamSpec, _MethodResultT]
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

    def __get__(
        self,
        instance: Any,
        owner: Any = None,
    ) -> Any:
        if isinstance(instance, SyncClient):
            return BoundSyncMethod(self._spec, instance)
        elif isinstance(instance, AsyncClient):
            return BoundAsyncMethod(self._spec, instance)
        else:
            raise TypeError()
