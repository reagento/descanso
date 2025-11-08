import asyncio
from dataclasses import dataclass
from datetime import datetime
from pprint import pprint
from typing import reveal_type

from adaptix import Retort
from aiohttp import ClientSession
from requests import Session

from descanso.http.aiohttp import AiohttpClient
from descanso.http.requests import RequestsClient
from descanso.request_transformers import Header, Url, Query
from descanso.rest import get


@dataclass
class MyResp:
    url: str
    repository_url: str
    id: int
    created_at: datetime


class MyClient:
    @get(
        Url("repos/reagento/dishka/issues"),
        Query("per_page", "1"),
        Header("Accept", "application/vnd.github+json"),
    )
    def foo(self, a: str) -> list[MyResp]:
        raise NotImplementedError


class MySyncClient(MyClient, RequestsClient):
    request_body_factory = Retort()
    response_body_factory = Retort()


class MyAsyncClient(MyClient, AiohttpClient):
    request_body_factory = Retort()
    response_body_factory = Retort()


async def main() -> None:
    pprint(MyClient.foo)

    # sync
    client = MySyncClient(
        base_url="https://api.github.com/", session=Session()
    )
    response = client.foo("1")
    reveal_type(client.foo)
    reveal_type(response)
    print(response)

    # async
    async with ClientSession() as session:
        aclient = MyAsyncClient(
            base_url="https://api.github.com/", session=session
        )
        response = await aclient.foo("1")
        reveal_type(aclient.foo)
        reveal_type(response)
        print(response)


asyncio.run(main())
