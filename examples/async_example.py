import asyncio
import logging
from dataclasses import dataclass
from io import BytesIO
from typing import Any

import aiohttp
from adaptix import NameStyle, Retort, name_mapping
from aiohttp import ClientSession

from descanso.http.aiohttp import AiohttpClient
from descanso.request_transformers import File
from descanso.rest_builder import RestBuilder


@dataclass
class Todo:
    id: int
    user_id: int
    title: str
    completed: bool


retort = Retort(recipe=[
    name_mapping(name_style=NameStyle.CAMEL),
])
rest = RestBuilder(
    request_body_dumper=retort,
    response_body_loader=retort,
    query_param_dumper=Retort(),
)

class RealAsyncClient(AiohttpClient):
    def __init__(self, session: ClientSession):
        super().__init__(
            base_url="https://jsonplaceholder.typicode.com/",
            session=session,
        )

    @rest.get("todos/{id}")
    async def get_todo(self, id: str) -> Todo:
        """GET method with path param"""

    @rest.get("todos")
    async def list_todos(self, user_id: int | None) -> list[Todo]:
        """GET method with query params"""

    @rest.delete("todos/{id}")
    async def delete_todo(self, id: int):
        """DELETE method"""

    @rest.post("todos")
    async def create_todo(self, body: Todo) -> Todo:
        """POST method"""

    @rest.get("https://httpbin.org/get")
    async def get_httpbin(self) -> Any:
        """Url different from base_url"""

    @rest.post(
        "https://httpbin.org/post",
        File("file"),
    )
    async def upload_image(self, file: BytesIO):
        """Sending binary data"""


async def main():
    async with aiohttp.ClientSession() as session:
        logging.basicConfig(level=logging.DEBUG)
        client = RealAsyncClient(session)
        print(RealAsyncClient.list_todos)
        print()
        print(await client.list_todos(user_id=1))
        print(await client.get_todo(id="1"))
        print(await client.delete_todo(1))
        print(await client.create_todo(
            Todo(123456789, 111222333, "By Tishka17", False)))

        with open("example.py", "rb") as f:
            print(await client.upload_image(f))


loop = asyncio.get_event_loop()
loop.run_until_complete(main())
