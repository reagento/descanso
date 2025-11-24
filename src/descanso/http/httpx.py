from collections.abc import AsyncIterator, Iterator, Sequence
from contextlib import asynccontextmanager, contextmanager
from typing import IO, Any, Generic, Self, TypeVar

from httpx import URL, QueryParams, Response
from httpx import AsyncClient as _AsyncClient
from httpx import Client as _Client
from kiss_headers import parse_it

from descanso.client import (
    AsyncClient,
    AsyncResponseWrapper,
    BaseClient,
    SyncClient,
    SyncResponseWrapper,
)
from descanso.request import (
    FileData,
    HttpRequest,
    KeyValueList,
    RequestTransformer,
)
from descanso.response import ResponseTransformer

_HttpxClientT = TypeVar("_HttpxClientT", _Client, _AsyncClient)

_FileName = str | None
_FileContent = IO[bytes] | bytes | str
_FileContentType = str | None
_HttpxFile = (
    _FileContent
    | tuple[_FileName, _FileContent]
    | tuple[_FileName, _FileContent, _FileContentType]
)


class HttpxResponseWrapper(SyncResponseWrapper, AsyncResponseWrapper):
    def __init__(self: Self, response: Response) -> None:
        self.status_code = response.status_code
        self.status_text = response.reason_phrase
        self.url = str(response.url)
        self.headers = parse_it(response.headers)
        self.body = None
        self._raw_response = response

    def load_body(self: Self) -> None:
        self.body = self._raw_response.content

    async def aload_body(self: Self) -> None:
        self.body = self._raw_response.content


class BaseHttpxClient(BaseClient, Generic[_HttpxClientT]):
    def __init__(
        self: Self,
        session: _HttpxClientT,
        base_url: str | None = None,
        transformers: Sequence[RequestTransformer | ResponseTransformer] = (),
    ) -> None:
        super().__init__(
            transformers=transformers,
        )

        self._base_url = base_url
        self._session: _HttpxClientT = session

    @contextmanager
    def _override_base_url(self: Self) -> Iterator[None]:
        old: URL = self._session.base_url

        if self._base_url is not None:
            self._session.base_url = self._base_url

        yield

        if old != self._session.base_url:
            self._session.base_url = old

    def _to_httpx_query_params(
        self: Self,
        params: KeyValueList[Any],
    ) -> QueryParams:
        httpx_params = []

        for key, value in params:
            if value is None:
                continue
            httpx_params.append((key, value))

        return QueryParams(httpx_params)

    def _to_httpx_files(
        self: Self,
        files: KeyValueList[FileData],
    ) -> KeyValueList[_HttpxFile]:
        httpx_files: KeyValueList[_HttpxFile] = []

        for key, file in files:
            if file.contents is None:
                continue

            file_payload = (
                file.filename,
                file.contents,
                file.content_type,
            )

            httpx_files.append((key, file_payload))

        return httpx_files


class HttpxClient(SyncClient, BaseHttpxClient[_Client]):
    @contextmanager
    def send_request(
        self: Self,
        request: HttpRequest,
    ) -> Iterator[SyncResponseWrapper]:
        with self._override_base_url():
            response = self._session.request(
                method=request.method,
                url=request.url,
                headers=request.headers.items(),
                data=request.body,
                params=self._to_httpx_query_params(request.query_params),
                files=self._to_httpx_files(request.files),
            )

        yield HttpxResponseWrapper(response)


class AsyncHttpxClient(AsyncClient, BaseHttpxClient[_AsyncClient]):
    @asynccontextmanager
    async def asend_request(
        self: Self,
        request: HttpRequest,
    ) -> AsyncIterator[AsyncResponseWrapper]:
        with self._override_base_url():
            response = await self._session.request(
                method=request.method,
                url=request.url,
                headers=request.headers.items(),
                data=request.body,
                params=self._to_httpx_query_params(request.query_params),
                files=self._to_httpx_files(request.files),
            )

        yield HttpxResponseWrapper(response)
