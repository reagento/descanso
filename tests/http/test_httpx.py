from typing import Any

import pytest
import pytest_asyncio
from httpx import AsyncClient, Client

from descanso import RestBuilder
from descanso.http.httpx import AsyncHttpxClient, HttpxClient
from descanso.jsonrpc import JsonRPCBuilder, JsonRPCError
from .data import req_resp


@pytest_asyncio.fixture
def sync_session():
    with Client() as session:
        yield session


@pytest_asyncio.fixture
async def async_session():
    async with AsyncClient() as session:
        yield session


@pytest_asyncio.fixture
def sync_client(server_addr, sync_session):
    yield HttpxClient(base_url=server_addr, session=sync_session)


@pytest_asyncio.fixture
async def async_client(server_addr, async_session):
    yield AsyncHttpxClient(base_url=server_addr, session=async_session)


@pytest.mark.parametrize(("req", "expected_resp"), req_resp())
def test_sync_httpx(sync_client, req, expected_resp):
    with sync_client.send_request(req) as resp:
        resp.load_body()
        assert resp == expected_resp


@pytest.mark.parametrize(("req", "expected_resp"), req_resp())
@pytest.mark.asyncio
async def test_async_httpx(async_client, req, expected_resp):
    async with async_client.asend_request(req) as resp:
        await resp.aload_body()
        assert resp == expected_resp


def test_rest_httpx(server_addr, sync_session):
    rest = RestBuilder()

    class Client(HttpxClient):
        @rest.get("/json")
        def do_get(self, body: dict) -> dict: ...

    client = Client(server_addr, sync_session)
    resp = client.do_get({"x": 1})
    assert resp == {"y": 2}


@pytest.mark.asyncio
async def test_rest_httpx_async(server_addr, async_session):
    rest = RestBuilder()

    class Client(AsyncHttpxClient):
        @rest.get("/json")
        def do_get(self, body: dict) -> dict: ...

    client = Client(server_addr, async_session)
    resp = await client.do_get({"x": 1})
    assert resp == {"y": 2}


@pytest.mark.asyncio
async def test_jsonrpc_httpx_async(server_addr, async_session):
    jsonrpc = JsonRPCBuilder(url="jsonrpc")

    class Client(AsyncHttpxClient):
        @jsonrpc("good")
        def do_good(self, body: Any) -> Any: ...

        @jsonrpc("bad")
        def do_bad(self) -> Any: ...

        @jsonrpc("invalid")
        def do_invalid(self) -> Any: ...

    client = Client(server_addr, async_session)
    resp = await client.do_good([42])
    assert resp == 42

    with pytest.raises(JsonRPCError) as e:
        await client.do_bad()
    assert e.value.code == -32000
    assert e.value.message == "My error"

    with pytest.raises(JsonRPCError) as e:
        await client.do_invalid()
    assert e.value.code == -32601
    assert e.value.message == "Method not found"
