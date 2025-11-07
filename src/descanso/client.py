
from descanso.request import HttpRequest
from descanso.response import HttpResponse


class SyncClient:
    def send_request(self, request: HttpRequest) -> HttpResponse:
        raise NotImplementedError


class AsyncClient:
    async def asend_request(self, request: HttpRequest) -> HttpResponse:
        raise NotImplementedError
