import json
from collections.abc import Sequence
from typing import Any

from .client import Loader
from .exceptions import ClientError, ServerError
from .response import HttpResponse, ResponseTransformer


class BodyModelLoad(ResponseTransformer):
    def __init__(
        self,
        type_hint: Any,
        loader: Loader | None,
        codes: Sequence[int] = (200,),
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
        response.body = self.loader.load(response.body, self.type_hint)
        return response

    def __repr__(self):
        return (
            f"{self.__class__.__name__}"
            f"("
            f"{self.type_hint!r}, "
            f"codes={self.codes!r}, "
            f"loader={self.loader!r}"
            f")"
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
        except_codes: Sequence[int] | None = None,
        need_body: bool = False,
    ) -> None:
        self._need_body = need_body
        self.codes = codes
        self.except_codes = except_codes

    def need_response_body(self, response: HttpResponse) -> bool:
        return self._need_body

    def transform_response(
        self,
        response: HttpResponse,
        fields: dict[str, Any],
    ) -> HttpResponse:
        if (
            not self.codes and response.status_code >= 400  # noqa: PLR2004
        ) or not self._is_status_code_allowed(response.status_code):
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

    def _is_status_code_allowed(self, code: int) -> bool:
        if self.except_codes and code not in self.except_codes:
            return False

        if self.codes and code in self.codes:
            return False

        return True

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
