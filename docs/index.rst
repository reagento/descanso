Descanso
=======================================

A modern and simple way to create HTTP clients.

You do not need to write trivial http processing again and again. Just write method signature, mark some templates and that's it.
It works both in sync and async style.

Request/response processing is highly customizable, you can even build your own pipelines (e.g. for JSON RPC) and even mix several styles within one client class.

.. code-block:: python

    class Client(RequestsClient):
        @rest.get("todos/{id}")
        def get_todo(self, id: int) -> Todo:
            pass

    client = Client("http://example.com", Session())
    todo = client.get(42)

To find out how to use it, follow to :ref:`quickstart`

.. toctree::
   :hidden:
   :caption: Contents:

   quickstart
   configuration
   jsonrpc
   auth
   transports
   migration_from_dcr

.. toctree::
    :hidden:
    :caption: Project Links

    GitHub <https://github.com/reagento/descanso>
    PyPI <https://pypi.org/project/descanso>
    Chat <https://t.me/reagento_ru>
