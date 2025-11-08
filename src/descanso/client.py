from typing import AsyncContextManager, ContextManager

from descanso.request import HttpRequest
from descanso.response import HttpResponse


class SyncResponseWrapper(HttpResponse):
    def load_body(self) -> None:
        raise NotImplementedError


class SyncClient:
    def send_request(
        self,
        request: HttpRequest,
    ) -> ContextManager[SyncResponseWrapper]:
        raise NotImplementedError


class AsyncResponseWrapper(HttpResponse):
    async def aload_body(self) -> None:
        raise NotImplementedError


class AsyncClient:
    def asend_request(
        self,
        request: HttpRequest,
    ) -> AsyncContextManager[AsyncResponseWrapper]:
        raise NotImplementedError
