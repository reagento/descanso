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
        "repos/reagento/dishka/issues",
        Query("per_page", "1"),
        Header("Accept", "application/vnd.github+json"),
    )
    def foo(self, a: str) -> list[MyResp]:
        raise NotImplementedError


class MySyncClient(MyClient, RequestsClient):
    def __init__(self, base_url: str, session: Session) -> None:
        super().__init__(
            base_url=base_url,
            session=session,
            request_body_dumper=Retort(),
            request_params_dumper=Retort(),
            response_body_loader=Retort(),
        )


class MyAsyncClient(MyClient, AiohttpClient):
    def __init__(self, base_url: str, session: ClientSession) -> None:
        super().__init__(
            base_url=base_url,
            session=session,
            request_body_dumper=Retort(),
            request_params_dumper=Retort(),
            response_body_loader=Retort(),
        )


async def main() -> None:
    pprint(MyClient.foo)

    # sync
    client = MySyncClient(
        base_url="https://api.github.com/",
        session=Session(),
    )
    response = client.foo("1")
    reveal_type(client.foo)
    reveal_type(response)
    print(response)

    # async
    async with ClientSession() as session:
        aclient = MyAsyncClient(
            base_url="https://api.github.com/",
            session=session,
        )
        response = await aclient.foo("1")
        reveal_type(aclient.foo)
        reveal_type(response)
        print(response)


asyncio.run(main())
