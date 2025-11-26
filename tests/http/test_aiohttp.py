import aiohttp
import pytest
import pytest_asyncio

from descanso import RestBuilder
from descanso.http.aiohttp import AiohttpClient
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
async def test_rest_httpx_async(server_addr, session):
    rest = RestBuilder()

    class Client(AiohttpClient):
        @rest.get("/json")
        def do_get(self, body: dict) -> dict: ...

    client = Client(server_addr, session)
    resp = await client.do_get({"x": 1})
    assert resp == {"y": 2}
