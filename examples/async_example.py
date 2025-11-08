import asyncio
import logging
from dataclasses import dataclass
from io import BytesIO
from typing import Any

import aiohttp
from adaptix import NameStyle, Retort, name_mapping
from aiohttp import ClientSession

from descanso import delete, get, post
from descanso.http.aiohttp import AiohttpClient
from descanso.request_transformers import File


@dataclass
class Todo:
    id: int
    user_id: int
    title: str
    completed: bool


class RealAsyncClient(AiohttpClient):
    def __init__(self, session: ClientSession):
        retort = Retort(recipe=[
            name_mapping(name_style=NameStyle.CAMEL)
        ])
        super().__init__(
            base_url="https://jsonplaceholder.typicode.com/",
            session=session,
            request_body_dumper=retort,
            request_params_dumper=Retort(),
            response_body_loader=retort,
        )

    @get("todos/{id}")
    async def get_todo(self, id: str) -> Todo:
        pass

    @get("todos")
    async def list_todos(self, user_id: int | None) -> list[Todo]:
        pass

    @delete("todos/{id}")
    async def delete_todo(self, id: int):
        pass

    @post("todos")
    async def create_todo(self, body: Todo) -> Todo:
        """Создаем Todo"""

    @get("https://httpbin.org/get")
    def get_httpbin(self) -> Any:
        """Используем другой base_url"""

    @post(
        "https://httpbin.org/post",
        File("file"),
    )
    def upload_image(self, file: BytesIO):
        """Загружаем картинку"""


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
