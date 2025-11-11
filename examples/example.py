import logging
from dataclasses import dataclass
from io import BytesIO
from typing import Any

from adaptix import NameStyle, Retort, name_mapping
from requests import Session

from descanso.http.requests import RequestsClient
from descanso.request_transformers import File
from descanso.rest_builder import RestBuilder


@dataclass
class Todo:
    id: int
    user_id: int
    title: str
    completed: bool


retort = Retort(
    recipe=[
        name_mapping(name_style=NameStyle.CAMEL),
    ]
)
rest = RestBuilder(
    request_body_dumper=retort,
    response_body_loader=retort,
    query_param_dumper=Retort(),
)


class RealClient(RequestsClient):
    def __init__(self):
        super().__init__(
            base_url="https://jsonplaceholder.typicode.com/",
            session=Session(),
        )

    @rest.get("todos/{id}")
    def get_todo(self, id: str) -> Todo:
        """GET method with path param"""

    @rest.get("todos")
    def list_todos(self, user_id: int | None) -> list[Todo]:
        """GET method with query params"""

    @rest.delete("todos/{id}")
    def delete_todo(self, id: int):
        """DELETE method"""

    @rest.post("todos")
    async def create_todo(self, body: Todo) -> Todo:
        """POST method"""

    @rest.get("https://httpbin.org/get")
    def get_httpbin(self) -> Any:
        """Url different from base_url"""

    @rest.post(
        "https://httpbin.org/post",
        File("file"),
    )
    def upload_image(self, file: BytesIO):
        """Sending binary data"""


logging.basicConfig(level=logging.INFO)
client = RealClient()
print(client.list_todos(user_id=1))
print(client.get_todo(id="1"))
print(client.delete_todo(1))
print(client.create_todo(Todo(123456789, 111222333, "By Tishka17", False)))
print(client.get_httpbin())
with open("example.py", "rb") as f:
    print(client.upload_image(f))
