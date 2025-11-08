import logging
from typing import Optional, List

from pydantic import BaseModel, TypeAdapter, ConfigDict
from requests import Session

from descanso import get, post, delete
from descanso.client import Loader, Dumper
from descanso.http.requests import RequestsClient


class PydanticAdapter(Loader, Dumper):
    def load(self, data, type_):
        return TypeAdapter(type_).validate_python(data)

    def dump(self, data, type_):
        return TypeAdapter(type_).dump_python(data)


def to_camel(string: str) -> str:
    words = string.split('_')
    return words[0] + ''.join(word.capitalize() for word in words[1:])


class Todo(BaseModel):
    id: int
    user_id: int
    title: str
    completed: bool

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )


class RealClient(RequestsClient):
    def __init__(self):
        adapter = PydanticAdapter()
        super().__init__(
            base_url="https://jsonplaceholder.typicode.com/",
            session=Session(),
            request_body_dumper=adapter,
            request_params_dumper=adapter,
            response_body_loader=adapter,
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
        """Create Todo"""

    @get("https://httpbin.org/get")
    def get_httpbin(self):
        """Request with different base_url"""


logging.basicConfig(level=logging.INFO)
client = RealClient()
print(client.list_todos(user_id=1))
print(client.get_todo(id="1"))
print(client.delete_todo(1))
print(client.create_todo(Todo(
    id=123456789, user_id=111222333, title="By Tishka17", completed=False,
)))
print(client.get_httpbin())
