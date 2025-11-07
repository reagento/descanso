import inspect
from typing import Callable, List, get_type_hints, Any, Sequence

from .methodspec import MethodSpec
from .request import RequestTransformer, Field, FieldDestintation
from .request_transformers import Body, Query, JsonDump, RetortDump, Method
from .response import ResponseTransformer, HttpResponse
from .response_transofrmers import (
    RetortLoad,
    JsonLoad,
    ErrorRaiser,
    KeepResponse,
)


def get_default_request_transformers(
    fields: list[Field],
    default_body_name: str,
    is_json: bool,
    method: str,
) -> list[RequestTransformer]:
    transformers = []
    body_name = next(
        (field.name is FieldDestintation.BODY for field in fields), None
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


def get_func_fields(func: Callable, *, is_in_class) -> list[Field]:
    fields = []
    signature = inspect.signature(func)
    hints = get_type_hints(func)
    for arg in signature.parameters.values():
        fields.append(
            Field(
                name=arg.name,
                type_hint=hints.get(arg.name, Any),
                dest=FieldDestintation.UNDEFINED,
            )
        )
    if is_in_class:
        del fields[0]
    return fields


def get_request_transformers(
    func: Callable,
    *,
    transformers: List[RequestTransformer],
    body_name: str = "body",
    is_in_class: bool = True,
    is_json: bool = True,
    method: str = "GET",
) -> list[RequestTransformer]:
    fields = get_func_fields(func, is_in_class=is_in_class)
    for transformer in transformers:
        fields = transformer.transform_fields(fields)
    transformers.extend(
        get_default_request_transformers(
            fields, default_body_name=body_name, is_json=is_json, method=method
        )
    )
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


def get_response_transformers(
    func: Callable,
    *,
    transformers: List[ResponseTransformer],
    is_json: bool = True,
) -> list[ResponseTransformer]:
    hints = get_type_hints(func)
    result_hint = hints.get("return", Any)
    transformers = transformers.copy()
    transformers.extend(
        get_default_response_transformers(
            typehint=result_hint, is_json=is_json
        )
    )
    return transformers


def make_method_spec(
    func: Callable,
    transformers: Sequence[RequestTransformer | ResponseTransformer],
    is_json_request: bool = True,
    is_json_response: bool = True,
):
    return MethodSpec(
        func=func,
        name=func.__name__,
        doc=func.__doc__,
        request_transformers=get_request_transformers(
            func,
            transformers=[
                r for r in transformers if isinstance(r, RequestTransformer)
            ],
            is_json=is_json_request,
        ),
        response_transformers=get_response_transformers(
            func,
            transformers=[
                r for r in transformers if isinstance(r, ResponseTransformer)
            ],
            is_json=is_json_response,
        ),
    )
