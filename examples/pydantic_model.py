import logging

from pydantic import BaseModel, ConfigDict, TypeAdapter
from requests import Session

from descanso import delete, get, post
from descanso.client import Dumper, Loader
from descanso.http.requests import RequestsClient


class PydanticAdapter(Loader, Dumper):
    def load(self, data, type_):
        return TypeAdapter(type_).validate_python(data)

    def dump(self, data, type_):
        return TypeAdapter(type_).dump_python(data)


def to_camel(string: str) -> str:
    words = string.split("_")
    return words[0] + "".join(word.capitalize() for word in words[1:])


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
        """GET method with path param"""

    @get("todos")
    def list_todos(self, user_id: int | None) -> list[Todo]:
        """GET method with query params"""

    @delete("todos/{id}")
    def delete_todo(self, id: int):
        """DELETE method"""

    @post("todos")
    def create_todo(self, body: Todo) -> Todo:
        """POST method"""

    @get("https://httpbin.org/get")
    def get_httpbin(self):
        """Url different from base_url"""


logging.basicConfig(level=logging.INFO)
client = RealClient()
print(client.list_todos(user_id=1))
print(client.get_todo(id="1"))
print(client.delete_todo(1))
print(client.create_todo(Todo(
    id=123456789, user_id=111222333, title="By Tishka17", completed=False,
)))
print(client.get_httpbin())
