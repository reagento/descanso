from typing import Any


class HttpStatusError(RuntimeError):
    def __init__(self, status_code: int, status_text: str, body: Any):
        self.status_code = status_code
        self.status_text = status_text
        self.body = body

    def __repr__(self):
        return (
            f"{self.__class__.__name__}"
            f"({self.status_code}, {self.status_text!r}, {self.body!r})"
        )

    __str__ = __repr__


class ClientError(HttpStatusError):
    pass


class ServerError(HttpStatusError):
    pass
