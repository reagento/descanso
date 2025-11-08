from dataclasses import dataclass

import requests
import requests_mock

from descanso import get, post
from tests.requests.stubs import StubRequestsClient


def test_methods(session: requests.Session, mocker: requests_mock.Mocker):
    class Api(StubRequestsClient):
        @get("/get")
        def get_x(self) -> list[int]:
            raise NotImplementedError

        @post("/post")
        def post_x(self) -> list[int]:
            raise NotImplementedError

    mocker.get("https://example.com/get", text="[1,2]", complete_qs=True)
    mocker.post("https://example.com/post", text="[1,2,3]", complete_qs=True)
    client = Api(session=session)
    assert client.get_x() == [1, 2]
    assert client.post_x() == [1, 2, 3]


def test_path_params(session: requests.Session, mocker: requests_mock.Mocker):
    class Api(StubRequestsClient):
        @post("/post/{id}")
        def post_x(self, id) -> list[int]:
            raise NotImplementedError

    mocker.post("https://example.com/post/1", text="[1]", complete_qs=True)
    mocker.post("https://example.com/post/2", text="[1,2]", complete_qs=True)
    client = Api(session=session)
    assert client.post_x(1) == [1]
    assert client.post_x(2) == [1, 2]


def test_query_params(session: requests.Session, mocker: requests_mock.Mocker):
    class Api(StubRequestsClient):
        @post("/post/{id}")
        def post_x(self, id: str, param: int | None) -> list[int]:
            raise NotImplementedError

    mocker.post(
        url="https://example.com/post/x?",
        text="[0]",
        complete_qs=True,
    )
    mocker.post(
        url="https://example.com/post/x?param=1",
        text="[1]",
        complete_qs=True,
    )
    mocker.post(
        url="https://example.com/post/x?param=2",
        text="[1,2]",
        complete_qs=True,
    )
    client = Api(session=session)
    assert client.post_x("x", None) == [0]
    assert client.post_x("x", 1) == [1]
    assert client.post_x("x", 2) == [1, 2]


@dataclass
class RequestBody:
    x: int
    y: str


def test_body(session: requests.Session, mocker: requests_mock.Mocker):
    class Api(StubRequestsClient):
        @post("/post/")
        def post_x(self, body: RequestBody) -> None:
            raise NotImplementedError

    mocker.post(
        url="https://example.com/post/",
        text="null",
        complete_qs=True,
    )
    client = Api(session=session)
    assert client.post_x(RequestBody(x=1, y="test")) is None
    assert mocker.called_once
    assert mocker.request_history[0].json() == {"x": 1, "y": "test"}


def test_kwonly_param(session: requests.Session, mocker: requests_mock.Mocker):
    class Api(StubRequestsClient):
        @post("/post/")
        def post(
            self,
            *,
            body: RequestBody,
        ) -> None:
            raise NotImplementedError

        @get("/get/{id}")
        def get_x(self, *, id: str, param: str = "1") -> list[int]:
            raise NotImplementedError

    mocker.post(
        url="https://example.com/post/",
        text="null",
        complete_qs=True,
    )
    mocker.get(
        url="https://example.com/get/x?param=1",
        text="[0]",
        complete_qs=True,
    )
    client = Api(session=session)
    assert client.post(body=RequestBody(x=1, y="test")) is None
    assert mocker.called_once
    assert mocker.request_history[0].json() == {"x": 1, "y": "test"}

    assert client.get_x(id="x") == [0]
