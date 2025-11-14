.. _configuration:

Configuration
**************************

Each request is processed as a pipeline of multiple ``Transformers``. The order is following:

1. Request transformers set on method
2. Default request transformers (e.g from ``RestBuilder``)
3. Request transformers set on a client
4. Response transformers set on method
5. Default response transformers (e.g from  ``RestBuilder``)
6. Response transformers set on a client

Request configuration
===========================

Query parameters
--------------------------

To mark a method parameter as a query parameter use ``Query(name)`` transformer.

To generate a query parameter dynamically use ``Query(name, template)``. Template can be a Python Format-string or a function. E.g.

.. code-block:: python

    from descanso.request_transformers import Query
    from descanso import RestBuilder

    rest = RestBuilder()

    def offset_from_page(page: int) -> int:
        return page*10


    class Client:
        @rest.get(
            "/",
            Query("body"),
            Query("limit", lambda: 10),
            Query("offset", offset_from_page)
            Query("name_re", "{short_name}.*")
        )
        def get(self, body: int, page: int, short_name: str):
            ...


In case you are using complex objects as query parameters you might want to have sem serialized properly.

Firstly, you need to set ``Dumper`` for convertion dataclasses into simple dicts. It is done by ``query_param_dumper`` parameter of ``RestBuilder`` or method itself.

.. code-block:: python

    from adaptix import Retort
    from descanso improt RestBuilder


    rest = RestBuilder(
        query_param_dumper=Retort(),  # dumper for all methods
    )


    class Client:
        @rest.get(
            "/",
            query_param_dumper=Retort(),  # change dumper for single method
        )
        def foo(self, param: Model):
            ...


The next thing is to set the algorithm putting complex data into query. It is done by ``query_param_post_dump`` param.
You can select between:

* ``FormQuery`` (default for RestBuilder) - puts each list value and object field as a separate query parameter.
* ``DelimiterQuery`` - use delimiter to join values.
* ``DeepObjectQuery`` - use the form ``param[]`` for lists and ``param[field]`` for objects
* ``PhpStyleQuery`` - similar to ``DeepObjectQuery`` but uses list indices and can handle nested objects


Headers
-----------------------------------

Headers can be simply set in the same way as query parameters. Just use ``Header()`` transformer. The defference is that no additional processing is done automatically.

.. code-block:: python

    from descanso.request_transformers import Header
    from descanso import RestBuilder

    rest = RestBuilder()

    def offset_from_page(page: int) -> int:
        return page*10


    class Client:
        token = "xxx"

        @rest.get(
            "/",
            Header("Authorization", "Bearer {self.token}"),
            Query("X-MY_HEADER", lambda: "hello"),
        )
        def get(self):
            ...

Request body
-----------------------------------

To mark different parameter as a request body use ``Body(name)``

Body is also dumped from structure using ``Dumper`` set as ``request_body_dumper``. Do not forget to provide correct type hint on a method parameter.

After dumping body is converted to plain text using ``request_body_post_dump`` which is ``JsonDump`` by default for RestBuilder

.. code-block:: python

    from adaptix import Retort
    from descanso improt RestBuilder


    rest = RestBuilder(
        request_body_dumper=Retort(),
        request_body_post_dump=JsonDump(),
    )


    class Client:
        @rest.post("/", Body("data"))
        def send_data(self, data: Model) -> None:
            ...


Response configuration
===========================

Response body
-------------------------------

You can change ``response_body_pre_load`` to load raw data to python structure than processed by ``Loader``. By default, json is loaded using ``JsonLoad``


You can set ``response_body_loader`` to provide a ``Loader`` instance for converting structure to you dataclass or model accoridng to a return type hint.

.. code-block:: python

    from adaptix import Retort
    from descanso improt RestBuilder


    rest = RestBuilder(
        response_body_loader=Retort(),
        request_body_post_dump=JsonLoad(),
    )


    class Client:
        @rest.get("/")
        def send_data(self) -> Response:
            ...


To get full response with unprocessed body use ``HttpResponse`` as a method result type.


Status code
------------------------

Status code checkin is done by an ``ErrorRaiser`` class set as a ``error_raiser`` parameter.
