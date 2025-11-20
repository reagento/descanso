import aiohttp
import pytest
import pytest_asyncio

from descanso.http.aiohttp import AiohttpClient
from .data import req_resp


@pytest_asyncio.fixture
async def client(server_addr):
    async with aiohttp.ClientSession() as session:
        yield AiohttpClient(server_addr, session)


@pytest.mark.parametrize(["req", "expected_resp"], req_resp)
@pytest.mark.asyncio
async def test_requests(client, req, expected_resp):
    async with client.asend_request(req) as resp:
        await resp.aload_body()
        assert resp == expected_resp
