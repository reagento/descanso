__all__ = [
    "AsyncHttpxClient",
    "HttpxClient",
    "HttpxResponseWrapper",
]

import urllib.parse
from collections.abc import AsyncIterator, Iterator, Sequence
from contextlib import asynccontextmanager, contextmanager
from typing import IO, Any

from httpx import AsyncClient as _AsyncClient
from httpx import Client as _Client
from httpx import QueryParams, Response
from kiss_headers import parse_it

from descanso.client import (
    AsyncClient,
    AsyncResponseWrapper,
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
from descanso.utils import ensure_trailing_slash

_FileName = str | None
_FileContent = IO[bytes] | bytes | str
_FileContentType = str | None
_HttpxFile = (
    _FileContent
    | tuple[_FileName, _FileContent]
    | tuple[_FileName, _FileContent, _FileContentType]
)


class HttpxResponseWrapper(SyncResponseWrapper, AsyncResponseWrapper):
    def __init__(self, response: Response) -> None:
        self.status_code = response.status_code
        self.status_text = response.reason_phrase
        self.url = str(response.url)
        self.headers = parse_it(response.headers)
        self.body = None
        self._raw_response = response

    def load_body(self) -> None:
        self.body = self._raw_response.content

    async def aload_body(self) -> None:
        self.body = self._raw_response.content


def to_httpx_query_params(params: KeyValueList[Any]) -> QueryParams:
    httpx_params = []

    for key, value in params:
        if value is None:
            continue
        httpx_params.append((key, value))

    return QueryParams(httpx_params)


def to_httpx_files(files: KeyValueList[FileData]) -> KeyValueList[_HttpxFile]:
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


class HttpxClient(SyncClient):
    def __init__(
        self,
        base_url: str,
        session: _Client,
        transformers: Sequence[RequestTransformer | ResponseTransformer] = (),
    ) -> None:
        super().__init__(
            transformers=transformers,
        )

        self._base_url = ensure_trailing_slash(base_url)
        self._session = session

    @contextmanager
    def send_request(
        self,
        request: HttpRequest,
    ) -> Iterator[SyncResponseWrapper]:
        response = self._session.request(
            method=request.method,
            url=urllib.parse.urljoin(self._base_url, request.url),
            headers=request.headers.items(),
            data=request.body,
            params=to_httpx_query_params(request.query_params),
            files=to_httpx_files(request.files),
        )

        yield HttpxResponseWrapper(response)


class AsyncHttpxClient(AsyncClient):
    def __init__(
        self,
        base_url: str,
        session: _AsyncClient,
        transformers: Sequence[RequestTransformer | ResponseTransformer] = (),
    ) -> None:
        super().__init__(
            transformers=transformers,
        )

        self._base_url = ensure_trailing_slash(base_url)
        self._session = session

    @asynccontextmanager
    async def asend_request(
        self,
        request: HttpRequest,
    ) -> AsyncIterator[AsyncResponseWrapper]:
        response = await self._session.request(
            method=request.method,
            url=urllib.parse.urljoin(self._base_url, request.url),
            headers=request.headers.items(),
            data=request.body,
            params=to_httpx_query_params(request.query_params),
            files=to_httpx_files(request.files),
        )

        yield HttpxResponseWrapper(response)
