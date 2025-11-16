# Descanso

[![PyPI version](https://badge.fury.io/py/descanso.svg)](https://pypi.python.org/pypi/descanso)
[![Supported versions](https://img.shields.io/pypi/pyversions/descanso.svg)](https://pypi.python.org/pypi/descanso)
[![Downloads](https://img.shields.io/pypi/dm/descanso.svg)](https://pypistats.org/packages/descanso)
[![License](https://img.shields.io/github/license/reagento/descanso)](https://github.com/reagento/descanso/blob/master/LICENSE)
[![GitHub Actions Workflow Status](https://img.shields.io/github/actions/workflow/status/reagento/descanso/setup.yml)](https://github.com/reagento/descanso/actions)
[![Doc](https://readthedocs.org/projects/descanso/badge/?version=latest&style=flat)](https://descanso.readthedocs.io)
[![Telegram](https://img.shields.io/badge/💬-Telegram-blue)](https://t.me/reagento_ru)

A modern and simple way to create clients for REST like APIs



> If you are looking for `dataclass-rest`, this is the same project with a new name.
> 
> We had reworked it a lot, but old code is still available in a separate [branch](https://github.com/reagento/descanso/tree/dataclass-rest).


## Quickstart


**Step 1.** Install
```bash
pip install descanso requests
```


**Step 2.** Declare models

```python
from dataclasses import dataclass

@dataclass
class Todo:
    id: int
    user_id: int
    title: str
    completed: bool
```

**Step 3.** Select serialization library. We recommend using `adaptix`.

You need to have `Loader` and `Dumper` implementations, `adaptix.Retort` would be fine


**Step 4.** Configure RestBuilder instance. It is needed to reuse common step during request.

```python
from adaptix import Retort
from descanso import RestBuilder


rest = RestBuilder(
    request_body_dumper=Retort(),
    response_body_loader=Retort(),
    query_param_dumper=Retort(),
)
```


**Step 5.** Create client class. Use `RequestsClient` or `AiohttpClient`

```python
from descanso.http.requests import RequestsClient

class RealClient(RequestsClient):
    ...
```

**Step 6.** Declare methods using `rest.get`/`rest.post`/`rest.delete`/`rest.patch`/`rest.put` decorators. You can override RestBuilder params if needed. 
Type hints are required. Body of method is ignored.

Use any method arguments to format URL.
`body` argument is sent as request body with json. Other arguments, not used in the URL are passed as query parameters.

```python
from descanso.http.requests import RequestsClient

class RealClient(RequestsClient):
    @rest.get("todos/{id}")
    def get_todo(self, id: str) -> Todo:
        pass

    @rest.get("todos")
    def list_todos(self, user_id: int | None) -> list[Todo]:
        pass

    @rest.delete("todos/{id}")
    def delete_todo(self, id: int):
        pass

    @rest.post("todos")
    def create_todo(self, body: Todo) -> Todo:
        pass
```

**Step 7.** Create client instance and use it.

```python
from requests import Session

client = RealClient(
    base_url="https://example.com/api",
    session=Session()
)
client.get_todo(5)
```

## Asyncio

To use async client instead of sync:

1. Install `aiohttp` (instead of `requests`)
2. Change `descanso.http.requests.RequestsClient` to `descanso.http.aiohttp.AiohttpClient`
3. All methods will be async, but you can add `async` keyword to make it more verbose
