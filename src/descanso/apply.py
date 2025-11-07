from inspect import getcallargs
from typing import Any

from descanso.methodspec import MethodSpec
from descanso.request import HttpRequest
from descanso.response import HttpResponse


def make_request(spec: MethodSpec, args: dict[str, Any]) -> HttpRequest:
    request = HttpRequest()
    for transformer in spec.request_transformers:
        transformer.transform_request(request, args)
    return request


def make_response(
    spec: MethodSpec,
    response: HttpResponse,
    args: dict[str, Any],
) -> Any:
    for transformer in spec.response_transformers:
        response = transformer.transform_response(response, args)
    return response.body


class SyncClient:
    def send_request(self, request: HttpRequest) -> HttpResponse:
        raise NotImplementedError


class AsyncClient:
    async def send_request(self, request: HttpRequest) -> HttpResponse:
        raise NotImplementedError


def apply_sync(
    spec: MethodSpec,
    client: SyncClient,
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
) -> Any:
    args = getcallargs(spec.func, client, *args, **kwargs)
    request = make_request(spec, args)
    response = client.send_request(request)
    return make_response(spec, response, args)


async def apply_async(
    spec: MethodSpec,
    client: AsyncClient,
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
) -> Any:
    args = getcallargs(spec.func, client, *args, **kwargs)
    request = make_request(spec, args)
    response = await client.send_request(request)
    # TODO read body
    return make_response(spec, response, args)
