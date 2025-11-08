from collections.abc import Sequence
from contextlib import AbstractAsyncContextManager, AbstractContextManager
from typing import Any, Protocol

from descanso.request import HttpRequest, RequestTransformer
from descanso.response import HttpResponse, ResponseTransformer


class Dumper(Protocol):
    def dump(self, data: Any, class_: Any = None) -> Any:
        raise NotImplementedError


class Loader(Protocol):
    def load(self, data: Any, class_: Any) -> Any:
        raise NotImplementedError


class BaseClient:
    def __init__(
        self,
        transformers: Sequence[RequestTransformer | ResponseTransformer],
        request_body_dumper: Dumper,
        response_body_loader: Loader,
    ):
        self.request_transformers = [
            r for r in transformers if isinstance(r, RequestTransformer)
        ]
        self.response_transformers = [
            r for r in transformers if isinstance(r, ResponseTransformer)
        ]
        self.request_body_dumper = request_body_dumper
        self.response_body_loader = response_body_loader


class SyncResponseWrapper(HttpResponse):
    def load_body(self) -> None:
        raise NotImplementedError


class SyncClient(BaseClient):
    def send_request(
        self,
        request: HttpRequest,
    ) -> AbstractContextManager[SyncResponseWrapper]:
        raise NotImplementedError


class AsyncResponseWrapper(HttpResponse):
    async def aload_body(self) -> None:
        raise NotImplementedError


class AsyncClient(BaseClient):
    def asend_request(
        self,
        request: HttpRequest,
    ) -> AbstractAsyncContextManager[AsyncResponseWrapper]:
        raise NotImplementedError
