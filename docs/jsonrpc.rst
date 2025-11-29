JSON RPC
**************************

You can use ``descanso`` to write a JSON RPC client.

The logic is similar to REST-like case but you need to create
``JsonRPCBuilder`` instance and use it as a decorator.


.. code-block:: python

    from adaptix import Retort
    from descanso.request_transformers import Query
    from descanso import JsonRPCBuilder

    jsonrpc = JsonRPCBuilder(
        url="/endpoint",
        request_body_dumper=Retort(),
        response_body_loader=Retort(),
    )

    class Client:
        @jsonrpc("methodname")
        def get(self, body: ParamsModel) -> ResultModel:
            ...

It is expected that first parameter of decorator is method name sent in request,
while the only function parameter is the value of ``params``.
Request ID is generated automatically.

In case of error response received, ``JsonRPCError`` with corresponding fields will be raised.

You need to provide ``request_body_dumper`` and ``response_body_loader``
to convert models to something that can be serialized in json.

Many params except jsonrpc method name can be set both in builder and when applying a decorator


API
===========================

.. autoclass:: descanso.JsonRPCBuilder