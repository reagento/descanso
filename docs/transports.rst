HTTP Transport backends
==========================

Descanso supports different libraries to send HTTP requests. To switch between them you need to change parent class for you ``Client``.

For ``requests``

.. note::
    This backend requires the ``requests`` library to be installed.
    You can install it using pip:

    .. code-block:: bash

        pip install requests

.. code-block:: python

    from descanso import RestBuilder
    from descanso.http.requests import RequestsClient

    rest = RestBuilder()


    class Client(RequestsClient):
        @rest.get("/")
        def foo(): ...


For ``aiohttp``:

.. note::
    This backend requires the ``aiohttp`` library to be installed.
    You can install it using pip:

    .. code-block:: bash

        pip install aiohttp

.. code-block:: python

    from descanso import RestBuilder
    from descanso.http.aiohttp import AiohttpClient

    rest = RestBuilder()


    class Client(AiohttpClient):
        @rest.get("/")
        async def foo(): ...

Adding ``async`` in front of function is not obligatory, function method becomes async automatically based on client class


For ``httpx``:

.. note::
    This backend requires the ``httpx`` library to be installed.
    You can install it using pip:

    .. code-block:: bash

        pip install httpx

.. code-block:: python

    from descanso import RestBuilder
    from descanso.http.httpx import HttpxClient, AsyncHttpxClient

    rest = RestBuilder()

    class AsyncClient(AsyncHttpxClient):
        @rest.get("/")
        async def foo(): ...

    class SyncClient(HttpxClient):
        @rest.get("/")
        def foo(): ...


Reusing signatures between transports
----------------------------------------

You can declare base client class with all needed methods and just create multiple child classes.

Methods will be automatically converted to async if you use async client implementation.

.. code-block:: python

    from descanso import RestBuilder
    from descanso.http.requests import RequestsClient
    from descanso.http.aiohttp import AiohttpClient

    rest = RestBuilder()


    class BaseClient:
        @rest.get("/")
        def foo(): ...

    class AsyncClient(BaseClient, AiohttpClient):
        pass

    class SyncClient(BaseClient, RequestsClient):
        pass


Custom transport
----------------------------------

To implement custom HTTP transport you need to implement ``SyncResponseWrapper`` and ``SyncClient`` (or ``AsyncResponseWrapper`` and ``AsyncClient``).

The purpose of ``ResponseWrapper``-classes is to load response body lazily, while ``Client`` is responsible to sending requests.
