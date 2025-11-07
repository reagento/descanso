import json
from typing import Protocol, Any, Sequence

from .response import ResponseTransformer, HttpResponse


class LoaderProtocol(Protocol):
    def load(self, data: Any, class_: Any) -> Any:
        raise NotImplementedError


class RetortLoad(ResponseTransformer):
    def __init__(self, type_hint: Any, codes: Sequence[int] = (200,)) -> None:
        self.type_hint = type_hint
        self._codes = codes

    def need_response_body(self, response: HttpResponse) -> bool:
        return response.status_code in self._codes

    def transform_response(
        self, response: HttpResponse, fields: dict[str, Any]
    ) -> HttpResponse:
        factory: LoaderProtocol = fields["self"].response_body_factory
        response.body = factory.load(response, self.type_hint)
        return response

    def __repr__(self):
        return f"{self.__class__.__name__}({self.type_hint!r}, codes={self._codes!r})"


class JsonLoad(ResponseTransformer):
    def __init__(self, codes: Sequence[int] = (200,)):
        self._codes = codes

    def need_response_body(self, response: HttpResponse) -> bool:
        return response.status_code in self._codes

    def transform_response(
        self, response: HttpResponse, fields: dict[str, Any]
    ) -> HttpResponse:
        response.body = json.loads(response.body)
        return response

    def __repr__(self):
        return f"{self.__class__.__name__}()"


class ErrorRaiser(ResponseTransformer):
    def transform_response(
        self, response: HttpResponse, fields: dict[str, Any]
    ) -> HttpResponse:
        if response.status_code >= 400:
            raise Exception(
                f"Error: {response.status_code} {response.status_text}"
            )
        return response

    def __repr__(self):
        return f"{self.__class__.__name__}()"


class KeepResponse(ResponseTransformer):
    def __init__(self, need_body: bool):
        self._need_body = need_body

    def need_body(self, response: HttpResponse) -> bool:
        return self._need_body

    def transform_response(
        self, response: HttpResponse, fields: dict[str, Any]
    ) -> HttpResponse:
        return HttpResponse(
            url=response.url,
            status_code=response.status_code,
            status_text=response.status_text,
            headers=response.headers,
            body=response,
        )

    def __repr__(self):
        return f"{self.__class__.__name__}(need_body={self._need_body})"
