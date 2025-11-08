import logging
from dataclasses import dataclass
from io import BytesIO
from typing import Optional, List

from adaptix import Retort, name_mapping, NameStyle
from requests import Session

from descanso import get, post, delete
from descanso.http.requests import RequestsClient
from descanso.request_transformers import File


@dataclass
class Todo:
    id: int
    user_id: int
    title: str
    completed: bool


class RealClient(RequestsClient):
    def __init__(self):
        retort = Retort(recipe=[
            name_mapping(name_style=NameStyle.CAMEL)
        ])
        super().__init__(
            base_url="https://jsonplaceholder.typicode.com/",
            session=Session(),
            request_body_dumper=retort,
            request_params_dumper=Retort(),
            response_body_loader=retort,
        )

    @get("todos/{id}")
    def get_todo(self, id: str) -> Todo:
        pass

    @get("todos")
    def list_todos(self, user_id: Optional[int]) -> List[Todo]:
        pass

    @delete("todos/{id}")
    def delete_todo(self, id: int):
        pass

    @post("todos")
    def create_todo(self, body: Todo) -> Todo:
        """Создаем Todo"""

    @get("https://httpbin.org/get")
    def get_httpbin(self):
        """Используем другой base_url"""

    @post(
        "https://httpbin.org/post",
        File("file")
    )
    def upload_image(self, file: BytesIO):
        """Загружаем картинку"""


logging.basicConfig(level=logging.INFO)
client = RealClient()
print(client.list_todos(user_id=1))
print(client.get_todo(id="1"))
print(client.delete_todo(1))
print(client.create_todo(Todo(123456789, 111222333, "By Tishka17", False)))
print(client.get_httpbin())
with open("example.py", "rb") as f:
    print(client.upload_image(f))
