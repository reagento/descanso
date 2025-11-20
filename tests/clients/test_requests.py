import requests
import pytest
import pytest_asyncio

from descanso.http.requests import RequestsClient
from .data import req_resp


@pytest_asyncio.fixture
def client(server_addr):
    session = requests.Session()
    yield RequestsClient(server_addr, session)


@pytest.mark.parametrize(["req", "expected_resp"], req_resp)
def test_requests(client, req, expected_resp):
    with client.send_request(req) as resp:
        resp.load_body()
        assert resp == expected_resp
