import urllib.parse
from collections.abc import Iterator
from contextlib import contextmanager

from requests import Response, Session

from descanso.client import SyncClient, SyncResponseWrapper
from descanso.request import HttpRequest


class RequestsResponseWrapper(SyncResponseWrapper):
    def __init__(self, response: Response) -> None:
        self.status_code = response.status_code
        self.status_text = response.reason
        self.body = None
        self.headers = response.headers
        self._raw_response = response

    def load_body(self) -> None:
        self.body = self._raw_response.content


class RequestsClient(SyncClient):
    def __init__(self, base_url: str, session: Session) -> None:
        self._base_url = base_url
        self._session = session

    @contextmanager
    def send_request(
        self,
        request: HttpRequest,
    ) -> Iterator[SyncResponseWrapper]:
        resp = self._session.request(
            method=request.method,
            url=urllib.parse.urljoin(self._base_url, request.url),
            headers=dict(request.headers),
            data=request.body,
            params=request.query_params,
            files=request.files,
        )
        yield RequestsResponseWrapper(resp)
