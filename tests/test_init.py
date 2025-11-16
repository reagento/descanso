from dataclasses import dataclass
from typing import Any

import pytest
from aiohttp import ClientSession
from requests import Session

from descanso import Dumper, Loader, RestBuilder
from descanso.http.aiohttp import AiohttpClient
from descanso.http.requests import RequestsClient


@dataclass
class Todo:
    id: int


class StubConverter(Loader, Dumper):
    def load(self, data: Any, class_: Any) -> Any:
        return data

    def dump(self, data: Any, class_: Any) -> Any:
        return data


def test_sync():
    rest = RestBuilder()

    class RealClient(RequestsClient):
        def __init__(self):
            super().__init__(
                "https://jsonplaceholder.typicode.com/",
                Session(),
            )

        @rest.get("todos/{id}")
        def get_todo(self, id: str) -> Todo:
            pass

    assert RealClient()


@pytest.mark.asyncio
async def test_async():
    rest = RestBuilder()

    class RealClient(AiohttpClient):
        def __init__(self):
            super().__init__(
                "https://jsonplaceholder.typicode.com/",
                ClientSession(),
            )

        @rest.get("todos/{id}")
        async def get_todo(self, id: str) -> Todo:
            pass

        async def close(self):
            await self._session.close()

    client = RealClient()
    await client.close()
