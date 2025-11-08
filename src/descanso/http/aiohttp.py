import urllib.parse
from collections.abc import AsyncIterator, Sequence
from contextlib import asynccontextmanager

from aiohttp import ClientResponse, ClientSession, FormData

from descanso.client import (
    AsyncClient,
    AsyncResponseWrapper,
    Dumper,
    Loader,
)
from descanso.request import HttpRequest, RequestTransformer
from descanso.response import ResponseTransformer


class AiohttpResponseWrapper(AsyncResponseWrapper):
    def __init__(self, response: ClientResponse) -> None:
        self.status_code = response.status
        self.status_text = response.reason
        self.body = None
        self.headers = response.headers
        self._raw_response = response

    async def aload_body(self) -> None:
        self.body = await self._raw_response.read()


class AiohttpClient(AsyncClient):
    def __init__(
        self,
        base_url: str,
        session: ClientSession,
        request_body_dumper: Dumper,
        response_body_loader: Loader,
        transformers: Sequence[RequestTransformer | ResponseTransformer] = (),
    ) -> None:
        super().__init__(
            transformers=transformers,
            request_body_dumper=request_body_dumper,
            response_body_loader=response_body_loader,
        )
        self._base_url = base_url
        self._session = session

    @asynccontextmanager
    async def asend_request(
        self,
        request: HttpRequest,
    ) -> AsyncIterator[AsyncResponseWrapper]:
        data = request.body
        if request.files:
            data = FormData(data or {})
            for name, file in request.files:
                data.add_field(
                    name,
                    filename=file.filename,
                    content_type=file.content_type,
                    value=file.contents,
                )

        async with self._session.request(
            method=request.method,
            url=urllib.parse.urljoin(self._base_url, request.url),
            headers=dict(request.headers),
            data=data,
            params=request.query_params,
        ) as resp:
            yield AiohttpResponseWrapper(resp)
