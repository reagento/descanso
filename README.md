from adaptix import Retort

# Descanso

[![PyPI version](https://badge.fury.io/py/dataclass-rest.svg)](https://badge.fury.io/py/dataclass-rest)
[![Build Status](https://travis-ci.org/Tishka17/dataclass_rest.svg?branch=master)](https://travis-ci.org/Tishka17/dataclass_rest)

A modern and simple way to create clients for REST like APIs

## Quickstart


Step 1. Install
```bash
pip install descanso requests
```


Step 2. Declare models

```python
from dataclasses import dataclass

@dataclass
class Todo:
    id: int
    user_id: int
    title: str
    completed: bool
```

Step 3. Select serialization library. We recommend using `adaptix`.

You need to have `Loader` and `Dumper` implementations, `adaptix.Retort` would be fine


Step 4. Create and configure client

```python
from adaptix import Retort
from requests import Session
from descanso.http.requests import RequestsClient

class RealClient(RequestsClient):
    def __init__(self):
        super().__init__(
            base_url="https://example.com/api",
            session=Session(),
            request_params_dumper=Retort(),
            request_body_dumper=Retort(),
            response_body_loader=Retort(),
        )
```

Step 5. Declare methods using `get`/`post`/`delete`/`patch`/`put` decorators.
Type hints are required. Body of method is ignored.

Use any method arguments to format URL.
`body` argument is sent as request body with json. Other arguments, not used in URL are passed as query parameters.
`get` and `delete` does not have body.

```python
from typing import Optional, List
from adaptix import Retort
from requests import Session
from descanso import get, post, delete
from descanso.http.requests import RequestsClient

class RealClient(RequestsClient):
    def __init__(self):
        super().__init__(
            base_url="https://example.com/api",
            session=Session(),
            request_params_dumper=Retort(),
            request_body_dumper=Retort(),
            response_body_loader=Retort(),
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
        pass
```

You can use Callable ```(...) -> str``` as the url source,
all parameters passed to the client method can be obtained inside the Callable

```python
from adaptix import Retort
from requests import Session
from descanso import get
from descanso.http.requests import RequestsClient

def url_generator(todo_id: int) -> str:
    return f"/todos/{todo_id}/"


class RealClient(RequestsClient):
    def __init__(self):
        super().__init__(
            base_url="https://example.com/api",
            session=Session(),
            request_params_dumper=Retort(),
            request_body_dumper=Retort(),
            response_body_loader=Retort(),
        )

    @get(url_generator)
    def todo(self, todo_id: int) -> Todo:
        pass


client = RealClient()
client.todo(5)
```

## Asyncio

To use async client instead of sync:

1. Install `aiohttp` (instead of `requests`)
2. Change `descanso.http.requests.RequestsClient` to `descanso.http.aiohttp.AiohttpClient`
3. All methods will be async, but you can add `async` keyword to make it more verbose

## Configuration

TBD