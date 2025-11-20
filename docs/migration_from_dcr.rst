Migration from dataclass_rest
===========================================

Basic usage
---------------------

1. **Replace imports**

.. code-block:: python

    # dataclass-rest
    from dataclass_rest.http.requests import RequestsClient
    from dataclass_rest.http.aiohttp import AiohttpClient

    # descanso
    from descanso.http.requests import RequestsClient
    from descanso.http.aiohttp import AiohttpClient


2. **Create RestBuilder** for access to decorators.

.. code-block:: python

    # dataclass-rest
    from dataclass_rest import get

    class Client(RequestsClient):
        @get("/")
        def get_x(self) -> Model: ...

    # descanso
    from descanso import RestBuilder

    rest = RestBuilder()

    class Client(RequestsClient):
        @rest.get("/")
        def get_x(self) -> Model: ...


3. **Move factories from Client methods to RestBuilder**. As they are not reused across different purposes by default anymore.

.. code-block:: python

    # dataclass-rest
    class RealClient(RequestsClient):
        def _init_request_body_factory(self) -> Retort:
            return Retort(recipe=[
                name_mapping(name_style=NameStyle.CAMEL),
            ])

    # descanso
    retort = Retort(
        recipe=[
            name_mapping(name_style=NameStyle.CAMEL),
        ]
    )
    rest = RestBuilder(
        request_body_dumper=retort,
        response_body_loader=retort,
        query_param_dumper=retort,
    )


4. If you we changing **query parameter name** using ``Retort``, **map it manually**. You can do it per method or on the RestBuilder.

.. code-block:: python

    # dataclass-rest
    class RealClient(RequestsClient):
        def _init_request_args_factory(self) -> Retort:
            return Retort(recipe=[
                name_mapping(name_style=NameStyle.CAMEL),
            ])

        @get("/")
        def get_all(self, per_page: int) -> list[Model]: ...


    # descanso
    from descanso.request_transformers import Query

    class RealClient(RequestsClient):
        @rest.get("/", Query("perPage", "{per_page}"))
        def get_all(self, per_page: int) -> list[Model]: ...


5. **Replace** ``body_name`` with ``Body()``. You can do it per method or on the RestBuilder.

.. code-block:: python

    # dataclass-rest
    class RealClient(RequestsClient):
        @post("/", body_name="data")
        def get_all(self, data: Mode) -> None: ...

    # descanso
    from descanso.request_transformers import Body

    class RealClient(RequestsClient):
        @post("/", Body("data"))
        def get_all(self, data: Mode) -> None: ...

6. **Replace** ``send_json=False`` with ``request_body_post_dump=None``. You can do it per method or on the RestBuilder.

.. code-block:: python

    # dataclass-rest
    class RealClient(RequestsClient):
        @post("/", send_json=False)
        def get_all(self, body: str) -> None: ...

    # descanso
    from descanso.request_transformers import Body

    class RealClient(RequestsClient):
        @post("/", request_body_post_dump=None)
        def get_all(self, body: str) -> None: ...


Custom client and method classes
-----------------------------------------

In ``dataclass_rest`` part of request processing was done in Client class while another one is located in BoundMethod. In descanso you have 2 main things:

1. Client contains ``send_request`` or ``asend_request`` method. They send request and return ``SyncResponseWrapper``/``AsyncResponseWrapper`` instance
2. Response Wrapper is an extension to ``HttpResponse`` which allows you to load body during response processing.

Earlier you had several reasons to override methods

1. **Authorization**. See :ref:`authorization`

2. **Handling 204**. In descanso body is automatically skipped for responses with codes other than 200, 201, 202.
You can change it setting ``response_body_pre_load=JsonLoad(codes=(200, 201, 203, 204))``

3. **Retrieving body for errors**. Set ``error_raiser=ErrorRaiser(need_body=True)``


Handling 4xx and 5xx
-----------------------------

There is no more ``on_error`` helper in descanso. Instead you can set ``error_raiser`` which is executed before any other ``ResponseTransformer``.
You can use ``ErrorRaiser()`` customizing expected codes which are treated as errors or create own transformer.