from dataclasses import dataclass

import requests
import requests_mock

from descanso import get, post
from .stubs import StubRequestsClient


@dataclass
class ExampleBody:
    value: int


def test_string_hints(session: requests.Session, mocker: requests_mock.Mocker):
    class Api(StubRequestsClient):
        @get("/items/{item_id}")
        def get_item(self, item_id: "str") -> "list[int]":
            raise NotImplementedError

        @post("/items")
        def create_item(self, body: ExampleBody) -> "int | None":
            raise NotImplementedError

    mocker.get(
        "http://example.com/items/1",
        text="[1, 2, 3]",
        complete_qs=True,
    )
    mocker.post("http://example.com/items", text="1", complete_qs=True)

    client = Api(session=session)

    assert client.get_item("1") == [1, 2, 3]
    assert client.create_item(ExampleBody(value=5)) == 1
