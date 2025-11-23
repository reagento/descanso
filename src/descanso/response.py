from abc import abstractmethod
from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable

from kiss_headers import Headers

from .request import KeyValueList


@dataclass
class HttpResponse:
    status_code: int
    status_text: str
    url: str = ""
    headers: Headers = field(default_factory=Headers)
    body: Any = None


@runtime_checkable
class ResponseTransformer(Protocol):
    @abstractmethod
    def need_response_body(self, response: HttpResponse) -> bool:
        raise NotImplementedError

    @abstractmethod
    def transform_response(
        self,
        response: HttpResponse,
        fields: dict[str, Any],
    ) -> HttpResponse:
        raise NotImplementedError


class BaseResponseTransformer(ResponseTransformer):
    def need_response_body(self, response: HttpResponse) -> bool:
        return False

    def transform_response(
        self,
        response: HttpResponse,
        fields: dict[str, Any],
    ) -> HttpResponse:
        return response

    def __or__(self, other: ResponseTransformer) -> "PipeResponseTransformer":
        return PipeResponseTransformer(self, other)

    def __ror__(self, other: ResponseTransformer) -> "PipeResponseTransformer":
        return PipeResponseTransformer(other, self)


class PipeResponseTransformer(BaseResponseTransformer):
    def __init__(self, *others: ResponseTransformer) -> None:
        self.others = others

    def need_response_body(self, response: HttpResponse) -> bool:
        return any(other.need_response_body(response) for other in self.others)

    def transform_response(
        self,
        response: HttpResponse,
        fields: dict[str, Any],
    ) -> HttpResponse:
        for other in self.others:
            response = other.transform_response(response, fields)
        return response
