import json
from collections.abc import Sequence
from typing import Any

from .client import Loader
from .exceptions import ClientError, ServerError
from .response import HttpResponse, ResponseTransformer


class RetortLoad(ResponseTransformer):
    def __init__(
        self,
        type_hint: Any,
        codes: Sequence[int] = (200,),
        loader: Loader | None = None,
    ) -> None:
        self.type_hint = type_hint
        self.codes = codes
        self.loader = loader

    def need_response_body(self, response: HttpResponse) -> bool:
        return response.status_code in self.codes

    def transform_response(
        self,
        response: HttpResponse,
        fields: dict[str, Any],
    ) -> HttpResponse:
        if response.status_code not in self.codes:
            return response
        loader = self.loader or fields["self"].response_body_loader
        response.body = loader.load(response.body, self.type_hint)
        return response

    def __repr__(self):
        return (
            f"{self.__class__.__name__}"
            f"({self.type_hint!r}, codes={self.codes!r})"
        )


class JsonLoad(ResponseTransformer):
    def __init__(self, codes: Sequence[int] = (200,)):
        self.codes = codes

    def need_response_body(self, response: HttpResponse) -> bool:
        return response.status_code in self.codes

    def transform_response(
        self,
        response: HttpResponse,
        fields: dict[str, Any],
    ) -> HttpResponse:
        if response.status_code not in self.codes:
            return response
        response.body = json.loads(response.body)
        return response

    def __repr__(self):
        return f"{self.__class__.__name__}()"


class ErrorRaiser(ResponseTransformer):
    def __init__(
        self,
        *,
        codes: Sequence[int] | None = None,
        need_body: bool = False,
    ) -> None:
        self._need_body = need_body
        self.codes = codes

    def need_response_body(self, response: HttpResponse) -> bool:
        return self._need_body

    def transform_response(
        self,
        response: HttpResponse,
        fields: dict[str, Any],
    ) -> HttpResponse:
        if (
            self.codes is None and response.status_code >= 400   # noqa: PLR2004
        ) or (
            self.codes is not None and response.status_code in self.codes
        ):
            if response.status_code >= 500:  # noqa: PLR2004
                raise ServerError(
                    status_code=response.status_code,
                    status_text=response.status_text,
                    body=response.body,
                )

            raise ClientError(
                status_code=response.status_code,
                status_text=response.status_text,
                body=response.body,
            )
        return response

    def __repr__(self):
        return f"{self.__class__.__name__}()"


class KeepResponse(ResponseTransformer):
    def __init__(self, *, need_body: bool):
        self._need_body = need_body

    def need_body(self, response: HttpResponse) -> bool:
        return self._need_body

    def transform_response(
        self,
        response: HttpResponse,
        fields: dict[str, Any],
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
