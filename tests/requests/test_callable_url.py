import pytest
import requests
import requests_mock

from descanso import get
from .stubs import StubRequestsClient


def static_url() -> str:
    return "/get"


def param_url(entry_id: int) -> str:
    return f"/get/{entry_id}"


def kwonly_param_url(entry_id: int | None = None) -> str:
    if entry_id:
        return f"/get/{entry_id}"
    return "/get/random"


def test_simple(session: requests.Session, mocker: requests_mock.Mocker):
    class Api(StubRequestsClient):
        @get(static_url)
        def get_x(self) -> list[int]:
            raise NotImplementedError

    mocker.get("https://example.com/get", text="[1,2]", complete_qs=True)
    client = Api(session=session)
    assert client.get_x() == [1, 2]


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (
            1,
            1,
        ),
        (
            2,
            2,
        ),
    ],
)
def test_with_param(
    session: requests.Session,
    mocker: requests_mock.Mocker,
    value: int,
    expected: int,
):
    class Api(StubRequestsClient):
        @get(param_url)
        def get_entry(self, entry_id: int) -> int:
            raise NotImplementedError

    url = f"https://example.com/get/{expected}"
    mocker.get(url, text=str(expected), complete_qs=True)

    client = Api(session=session)
    assert client.get_entry(value) == expected


def test_excess_param(session: requests.Session, mocker: requests_mock.Mocker):
    class Api(StubRequestsClient):
        @get(param_url)
        def get_entry(
            self,
            entry_id: int,
            some_param: int | None = None,
        ) -> int:
            raise NotImplementedError

    mocker.get(
        "https://example.com/get/1?some_param=2",
        text="1",
        complete_qs=True,
    )

    client = Api(session=session)
    assert client.get_entry(1, 2) == 1


def test_kwonly_param(session: requests.Session, mocker: requests_mock.Mocker):
    class Api(StubRequestsClient):
        @get(kwonly_param_url)
        def get_entry(self, *, entry_id: int | None = None) -> int:
            raise NotImplementedError

    mocker.get("https://example.com/get/1", text="1", complete_qs=True)
    mocker.get("https://example.com/get/random", text="2", complete_qs=True)

    client = Api(session=session)
    assert client.get_entry(entry_id=1) == 1
    assert client.get_entry() == 2
