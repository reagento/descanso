import pytest
import requests_mock

from descanso import RestBuilder
from descanso.http import requests
from .stubs import StubConverter


@pytest.fixture
def session():
    return requests.Session()


@pytest.fixture
def mocker(session):
    with requests_mock.Mocker(
        session=session,
        case_sensitive=True,
    ) as session_mock:
        yield session_mock


@pytest.fixture
def rest():
    return RestBuilder(
        query_param_dumper=StubConverter(),
        request_body_dumper=StubConverter(),
        response_body_loader=StubConverter(),
    )
