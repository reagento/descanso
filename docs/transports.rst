HTTP Transport backends
==========================

Descanso supports different libraries to send HTTP requests. To switch between them you need to change parent class for you ``Client``.

For ``requests``

.. code:: python

    from descanso.http.requests import RequestsClient

    class Client(RequestsClient):
        @get("/")
        def foo(): ...

For ``aiohttp``:

.. code:: python

    from descanso.http.aiohttp import AiohttpClient

    class Client(AiohttpClient):
        @get("/")
        async def foo(): ...

Adding ``async`` in front of function is not obligatory, function method becomes async automatically based on client class


Custom transport
----------------------------------

To implement custom HTTP transport you need to implement ``SyncResponseWrapper`` and ``SyncClient`` (or their async siblings).

The purpose of ``ResponseWrapper``-classes is to load response body lazily, while ``Client`` is responsible to sending requests.