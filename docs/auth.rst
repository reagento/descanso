.. _authorization:

Authorization
===========================

There are a few approaches to have authorization:

**Static auth data**. Just add transformer corresponding to your logic.
You can reference ``self`` object to get data.
Note, that we are not using f-strings here, format string will be evaluated later.

.. code-block:: python

    class RequestsClient(SyncClient):
        def __init__(self, base_url: str, session: Session, token: str):
            super().__init__(
                base_url=base_url,
                session=session,
                transformers=[
                    Header("Authorization", "Bearer {self.token}")
                ]
            )
            self.token = token

**Dynamic auth data**. You need to redefine ``send_request`` or ``asend_request`` and implement token retrieval logic there.

.. code-block:: python

    class RequestsClient(RequestsClient):
        def send_request(
            self,
            request: HttpRequest,
        ) -> AbstractContextManager[SyncResponseWrapper]:
            token = get_token()  # custom logic here
            request.headers.append(("Authorization", f"Bearer {token}"))
            super().send_request(request)

**Basic authentication**. Use the :class:`~descanso.request_transformers.BasicAuth` transformer to add an ``Authorization`` header with the Basic scheme.
The ``from_credentials`` classmethod accepts constant login and password values.
Alternatively, provide templates (format strings or callables) that extract credentials from method arguments.

.. code-block:: python

    from descanso.request_transformers import BasicAuth

    class Client(SyncClient):
        def __init__(self, base_url: str, session: Session):
            super().__init__(
                base_url=base_url,
                session=session,
                transformers=[
                    BasicAuth.from_credentials("admin", "password")
                ]
            )

        # Templates that pull values from method args
        @rest.post(
            "/login",
            BasicAuth("{user}", "{password}"),
        )
        def login(self, user: str, password: str):
            ...