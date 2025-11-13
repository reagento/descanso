from dataclasses import dataclass
from typing import Any

import pytest
import requests
import requests_mock

from descanso import RestBuilder
from descanso.request import RequestTransformer
from descanso.request_transformers import (
    DeepObjectQuery,
    DelimiterQuery,
    FormQuery,
    PhpStyleQuery,
)
from tests.requests.stubs import StubRequestsClient


def test_methods(
    rest: RestBuilder,
    session: requests.Session,
    mocker: requests_mock.Mocker,
):
    class Api(StubRequestsClient):
        @rest.get("/get")
        def get_x(self) -> list[int]:
            raise NotImplementedError

        @rest.post("/post")
        def post_x(self) -> list[int]:
            raise NotImplementedError

    mocker.get("https://example.com/get", text="[1,2]", complete_qs=True)
    mocker.post("https://example.com/post", text="[1,2,3]", complete_qs=True)
    client = Api(session=session)
    assert client.get_x() == [1, 2]
    assert client.post_x() == [1, 2, 3]


def test_path_params(
    rest: RestBuilder,
    session: requests.Session,
    mocker: requests_mock.Mocker,
):
    class Api(StubRequestsClient):
        @rest.post("/post/{id}")
        def post_x(self, id) -> list[int]:
            raise NotImplementedError

    mocker.post("https://example.com/post/1", text="[1]", complete_qs=True)
    mocker.post("https://example.com/post/2", text="[1,2]", complete_qs=True)
    client = Api(session=session)
    assert client.post_x(1) == [1]
    assert client.post_x(2) == [1, 2]


def test_query_params(
    rest: RestBuilder,
    session: requests.Session,
    mocker: requests_mock.Mocker,
):
    class Api(StubRequestsClient):
        @rest.post("/post/{id}")
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


def test_body(
    rest: RestBuilder,
    session: requests.Session,
    mocker: requests_mock.Mocker,
):
    class Api(StubRequestsClient):
        @rest.post("/post/")
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


def test_kwonly_param(
    rest: RestBuilder,
    session: requests.Session,
    mocker: requests_mock.Mocker,
):
    class Api(StubRequestsClient):
        @rest.post("/post/")
        def post(
            self,
            *,
            body: RequestBody,
        ) -> None:
            raise NotImplementedError

        @rest.get("/get/{id}")
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


@pytest.mark.parametrize(
    ("transformer", "query"),
    [
        (DeepObjectQuery(), "ids[]=1&ids[]=2"),
        (FormQuery(), "ids=1&ids=2"),
        (DelimiterQuery(), "ids=1,2"),
        (DelimiterQuery("|"), "ids=1|2"),
    ],
)
def test_list_param(
    rest: RestBuilder,
    session: requests.Session,
    mocker: requests_mock.Mocker,
    transformer: RequestTransformer,
    query: str,
):
    class Api(StubRequestsClient):
        @rest.get("/", query_param_post_dump=transformer)
        def get(self, ids: list[int]) -> Any:
            raise NotImplementedError

    mocker.get(
        url=f"https://example.com/?{query}",
        text="[0]",
        complete_qs=True,
    )
    client = Api(session=session)
    assert client.get(ids=[1, 2])


@dataclass
class Param:
    a: int
    b: int


@pytest.mark.parametrize(
    ("transformer", "query"),
    [
        (DeepObjectQuery(), "x[a]=1&x[b]=2"),
        (FormQuery(), "a=1&b=2"),
        (DelimiterQuery(), "x=a,1,b,2"),
        (DelimiterQuery("|"), "x=a|1|b|2"),
    ],
)
def test_obj_param(
    rest: RestBuilder,
    session: requests.Session,
    mocker: requests_mock.Mocker,
    transformer: RequestTransformer,
    query: str,
):
    class Api(StubRequestsClient):
        @rest.get("/", query_param_post_dump=transformer)
        def get(self, x: Param) -> Any:
            raise NotImplementedError

    mocker.get(
        url=f"https://example.com/?{query}",
        text="[0]",
        complete_qs=True,
    )
    client = Api(session=session)
    assert client.get(x=Param(1, 2))


@dataclass
class MegaParam:
    a: int
    b: list[Param]


def test_php_param(
    rest: RestBuilder,
    session: requests.Session,
    mocker: requests_mock.Mocker,
):
    class Api(StubRequestsClient):
        @rest.get("/", query_param_post_dump=PhpStyleQuery())
        def get(self, x: MegaParam) -> Any:
            raise NotImplementedError

    mocker.get(
        url="https://example.com/?x[a]=1&x[b][0][a]=2&x[b][0][b]=3&x[b][1][a]=4&x[b][1][b]=5",
        text="[0]",
        complete_qs=True,
    )
    client = Api(session=session)
    assert client.get(
        x=MegaParam(
            a=1,
            b=[Param(2, 3), Param(4, 5)],
        ),
    )
