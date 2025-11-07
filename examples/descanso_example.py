import logging
import urllib.parse
from dataclasses import dataclass
from datetime import datetime
from pprint import pprint
from typing import Any

import requests
from adaptix import Retort

from descanso.client import SyncClient
from descanso.rest import get
from descanso.request import HttpRequest
from descanso.request_transformers import Header, Url, Query
from descanso.response import HttpResponse


class RequestsClient(SyncClient):
    base_ur: str

    def send_request(self, request: HttpRequest) -> HttpResponse:
        resp = requests.request(
            method=request.method,
            url=urllib.parse.urljoin(self.base_url, request.url),
            headers=dict(request.headers),
            data=request.body,
            params=request.query_params,
            files=request.files,
        )
        return HttpResponse(
            status_code=resp.status_code,
            status_text=resp.reason,
            body=resp.content,
            headers=resp.headers,
        )

    token = "xxx"


@dataclass
class MyResp:
    url: str
    repository_url: str
    id: int
    created_at: datetime


class MyClient:
    @get(
        Url("/repos/reagento/dishka/issues"),
        Query("per_page", "1"),
        Header("Accept", "application/vnd.github+json"),
    )
    def foo(self, a: str) -> list[MyResp]:
        pass


class MySynClient(MyClient, RequestsClient):
    base_url = "https://api.github.com/"
    request_body_factory = Retort()
    response_body_factory = Retort()


pprint(MyClient.foo)

client = MySynClient()
response = client.foo("1")
print(response)
