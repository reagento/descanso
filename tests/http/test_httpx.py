import pytest
import pytest_asyncio
from httpx import AsyncClient, Client

from descanso.http.httpx import AsyncHttpxClient, HttpxClient
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
