from collections.abc import Callable
from typing import (
    Any,
    ParamSpec,
    TypeVar,
)

from .method_descriptor import MethodBinder
from .request import Field, FieldDestintation, RequestTransformer
from .request_transformers import Body, JsonDump, Method, Query, RetortDump
from .response import HttpResponse, ResponseTransformer
from .response_transofrmers import (
    ErrorRaiser,
    JsonLoad,
    KeepResponse,
    RetortLoad,
)
from .signature import make_method_spec

_MethodResultT = TypeVar("_MethodResultT")
_MethodParamSpec = ParamSpec("_MethodParamSpec")

DEFAULT_BODY_PARAM = "body"


def get_default_request_transformers(
    fields: list[Field],
    default_body_name: str,
    is_json: bool,
    method: str,
) -> list[RequestTransformer]:
    transformers = []
    body_name = next(
        (field.name is FieldDestintation.BODY for field in fields),
        None,
    )

    for field in fields:
        if field.dest is not FieldDestintation.UNDEFINED:
            continue
        if not body_name and field.name == default_body_name:
            transformers.append(Body(field.name))
            body_name = default_body_name
        else:
            transformers.append(Query(field.name))
    if body_name:
        hint = next(
            (field.type_hint for field in fields if field.name == body_name),
            Any,
        )
        transformers.append(RetortDump(hint))
        if is_json:
            transformers.append(JsonDump())
    transformers.append(Method(method))
    return transformers


def get_default_response_transformers(
    *,
    typehint: Any,
    is_json: bool,
) -> list[ResponseTransformer]:
    transformers = []
    transformers.append(ErrorRaiser())
    if is_json:
        transformers.append(JsonLoad())
    if typehint is HttpResponse:
        transformers.append(KeepResponse(False))
    elif typehint is not Any and typehint is not object:
        transformers.append(RetortLoad(typehint))
    return transformers


def rest(
    *transformers: RequestTransformer | ResponseTransformer,
    method: str,
) -> Callable[
    [Callable[_MethodParamSpec, _MethodResultT]],
    MethodBinder[_MethodParamSpec, _MethodResultT],
]:
    def inner(
        func: Callable[_MethodParamSpec, _MethodResultT],
    ) -> MethodBinder[_MethodParamSpec, _MethodResultT]:
        spec = make_method_spec(
            func,
            transformers=transformers,
            is_in_class=True,
        )
        for transformer in spec.request_transformers:
            spec.fields = transformer.transform_fields(fields=spec.fields)
        spec.request_transformers.extend(
            get_default_request_transformers(
                fields=spec.fields,
                default_body_name=DEFAULT_BODY_PARAM,
                is_json=True,
                method=method,
            ),
        )
        spec.response_transformers.extend(
            get_default_response_transformers(
                typehint=spec.result_type,
                is_json=True,
            ),
        )

        return MethodBinder(spec)

    return inner


def get(
    *transformers: RequestTransformer | ResponseTransformer,
) -> Callable[
    [Callable[_MethodParamSpec, _MethodResultT]],
    MethodBinder[_MethodParamSpec, _MethodResultT],
]:
    return rest(*transformers, method="GET")


def post(
    *transformers: RequestTransformer | ResponseTransformer,
) -> Callable[
    [Callable[_MethodParamSpec, _MethodResultT]],
    MethodBinder[_MethodParamSpec, _MethodResultT],
]:
    return rest(*transformers, method="POST")
