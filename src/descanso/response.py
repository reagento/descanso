from abc import abstractmethod
from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable

from .request import KeyValueList


@dataclass
class HttpResponse:
    status_code: int
    status_text: str
    url: str = ""
    headers: KeyValueList[str | bytes] = field(default_factory=list)
    body: Any = None


@runtime_checkable
class ResponseTransformer(Protocol):
    def need_response_body(self, response: HttpResponse) -> bool:
        return False

    def transform_response(
        self, response: HttpResponse, fields: dict[str, Any]
    ) -> HttpResponse:
        return response
