from typing import Any

import aiohttp
import pytest
import pytest_asyncio

from descanso import RestBuilder
from descanso.http.aiohttp import AiohttpClient
from descanso.jsonrpc import JsonRPCBuilder, JsonRPCError
from .data import req_resp


@pytest_asyncio.fixture
async def session(server_addr):
    async with aiohttp.ClientSession() as session:
        yield session


@pytest.mark.parametrize(("req", "expected_resp"), req_resp())
@pytest.mark.asyncio
async def test_aiohttp(server_addr, session, req, expected_resp):
    client = AiohttpClient(server_addr, session)
    async with client.asend_request(req) as resp:
        await resp.aload_body()
        assert resp == expected_resp


@pytest.mark.asyncio
async def test_rest_aiohttp(server_addr, session):
    rest = RestBuilder()

    class Client(AiohttpClient):
        @rest.get("/json")
        def do_get(self, body: dict) -> dict: ...

    client = Client(server_addr, session)
    resp = await client.do_get({"x": 1})
    assert resp == {"y": 2}


@pytest.mark.asyncio
async def test_jsonrpc_aiohttp(server_addr, session):
    jsonrpc = JsonRPCBuilder(url="jsonrpc")

    class Client(AiohttpClient):
        @jsonrpc("good")
        def do_good(self, body: Any) -> Any: ...

        @jsonrpc("bad")
        def do_bad(self) -> Any: ...

        @jsonrpc("invalid")
        def do_invalid(self) -> Any: ...

    client = Client(server_addr, session)
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
