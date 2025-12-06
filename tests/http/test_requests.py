from typing import Any

import pytest
import pytest_asyncio
import requests

from descanso import RestBuilder
from descanso.http.requests import RequestsClient
from descanso.jsonrpc import JsonRPCBuilder, JsonRPCError
from .data import req_resp


@pytest_asyncio.fixture
def client(server_addr):
    session = requests.Session()
    yield RequestsClient(server_addr, session)


@pytest.mark.parametrize(("req", "expected_resp"), req_resp())
def test_requests(client, req, expected_resp):
    with client.send_request(req) as resp:
        resp.load_body()
        assert resp == expected_resp


def test_rest_requests(server_addr):
    rest = RestBuilder()

    class Client(RequestsClient):
        @rest.get("/json")
        def do_get(self, body: dict) -> dict: ...

    client = Client(server_addr, requests.Session())
    resp = client.do_get({"x": 1})
    assert resp == {"y": 2}


def test_jsonrpc_requests(server_addr):
    jsonrpc = JsonRPCBuilder(url="jsonrpc")

    class Client(RequestsClient):
        @jsonrpc(method="good")
        def do_good(self, body: Any) -> Any: ...

        @jsonrpc(method="bad")
        def do_bad(self) -> Any: ...

        @jsonrpc(method="invalid")
        def do_invalid(self) -> Any: ...

    client = Client(server_addr, requests.Session())
    resp = client.do_good([42])
    assert resp == 42

    with pytest.raises(JsonRPCError) as e:
        client.do_bad()
    assert e.value.code == -32000
    assert e.value.message == "My error"

    with pytest.raises(JsonRPCError) as e:
        client.do_invalid()
    assert e.value.code == -32601
    assert e.value.message == "Method not found"
