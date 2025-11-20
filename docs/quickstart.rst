.. _quickstart:


Quickstart
====================================


1. **Install descanso**


.. code-block:: shell

    pip install descanso requests


2. **Declare models for request and response body**

.. code-block:: python

    from dataclasses import dataclass

    @dataclass
    class Todo:
        id: int
        user_id: int
        title: str
        completed: bool

3. **Select serialization library.** We recommend using ``adaptix``.

You need to have ``descanso.Loader`` and ``descanso.Dumper`` implementations. Or just use ``adaptix.Retort``


4. **Configure RestBuilder instance.** It is needed to reuse common step during request.

.. code-block:: python

    from adaptix import Retort
    from descanso import RestBuilder

    rest = RestBuilder(
        request_body_dumper=Retort(),
        response_body_loader=Retort(),
        query_param_dumper=Retort(),
    )


5. **Create client class**. Use ``RequestsClient`` or ``AiohttpClient``

.. code-block:: python

    from descanso.http.requests import RequestsClient

    class RealClient(RequestsClient):
        ...

6. **Declare methods** using ``rest.get``/``rest.post``/``rest.delete``/``rest.patch``/``rest.put`` decorators.
Type hints are required. Body of method is ignored.

* First decorator params is an URL template as a python Format-string. You can reference any method params here (including self)
* By default, parameter called ``body`` is used as a request body.
* All other method params are treated as query params.
* Type hints are important

To customize this behavior refer :ref:`configuration`

.. code-block:: python

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

7. **Create client instance and use it.**

.. code-block:: python

    from requests import Session

    client = RealClient(
        base_url="https://example.com/api",
        session=Session()
    )
    client.get_todo(5)
