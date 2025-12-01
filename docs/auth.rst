.. _authorization:

Authorization
===========================

This section covers different approaches to add authentication to your API requests.

Static auth data
----------------------------

For static credentials stored in your client instance, use a transformer with a format string that references the client (``self``).
The format string is evaluated when the request is built, not when the client instance is created.

.. code-block:: python

    from descanso import SyncClient
    from descanso.request_transformers import Header

    class ApiClient(SyncClient):
        def __init__(self, base_url: str, session: Session, token: str):
            super().__init__(
                base_url=base_url,
                session=session,
                transformers=[
                    Header("Authorization", "Bearer {self.token}")
                ]
            )
            self.token = token

Dynamic auth data
----------------------------

For dynamic credentials that require custom retrieval logic (e.g., token refresh or rotation),
override the ``send_request`` or ``asend_request`` method and implement your authentication logic there.

.. code-block:: python

    from descanso import SyncClient
    from descanso.request import HttpRequest

    class ApiClient(SyncClient):
        def send_request(
            self,
            request: HttpRequest,
        ) -> AbstractContextManager[SyncResponseWrapper]:
            token = self._get_fresh_token()  # custom logic
            request.headers.append(("Authorization", f"Bearer {token}"))
            return super().send_request(request)

        def _get_fresh_token(self) -> str:
            # Implement token refresh or retrieval logic here
            ...

Basic authentication
----------------------------

For HTTP Basic authentication, use the :class:`~descanso.request_transformers.BasicAuth` transformer
to automatically encode credentials and add the ``Authorization`` header.

Use the ``from_credentials`` classmethod for constant username and password values.
For dynamic credentials, provide format string templates or callable templates that extract values from method arguments.

.. code-block:: python

    from descanso import SyncClient, RestBuilder
    from descanso.request_transformers import BasicAuth

    rest = RestBuilder()

    class Client(SyncClient):
        def __init__(self, base_url: str, session: Session):
            super().__init__(
                base_url=base_url,
                session=session,
                transformers=[
                    BasicAuth.from_credentials("admin", "password")
                ]
            )

        @rest.post(
            "/login",
            BasicAuth("{user}", "{password}"),
        )
        def login(self, user: str, password: str):
            ...