import urllib.parse
from collections.abc import Iterator, Sequence
from contextlib import contextmanager

from requests import Response, Session

from descanso.client import (
    SyncClient,
    SyncResponseWrapper,
)
from descanso.request import HttpRequest, RequestTransformer
from descanso.response import ResponseTransformer


class RequestsResponseWrapper(SyncResponseWrapper):
    def __init__(self, response: Response) -> None:
        self.status_code = response.status_code
        self.status_text = response.reason
        self.body = None
        self.headers = list(response.headers.items())
        self._raw_response = response

    def load_body(self) -> None:
        self.body = self._raw_response.content


class RequestsClient(SyncClient):
    def __init__(
        self,
        base_url: str,
        session: Session,
        transformers: Sequence[RequestTransformer | ResponseTransformer] = (),
    ) -> None:
        super().__init__(
            transformers=transformers,
        )
        self._base_url = base_url
        self._session = session

    @contextmanager
    def send_request(
        self,
        request: HttpRequest,
    ) -> Iterator[SyncResponseWrapper]:
        params = [(k, v) for k, v in request.query_params if v is not None]
        resp = self._session.request(
            method=request.method,
            url=urllib.parse.urljoin(self._base_url, request.url),
            headers=dict(request.headers),
            data=request.body,
            params=params,
            files=[
                (name, (data.filename, data.contents, data.content_type))
                for name, data in request.files
            ],
        )
        yield RequestsResponseWrapper(resp)
