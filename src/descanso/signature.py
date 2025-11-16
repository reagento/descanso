import inspect
from collections.abc import Callable, Sequence
from typing import Any, get_type_hints

from .method_spec import MethodSpec
from .request import FieldIn, RequestTransformer
from .response import ResponseTransformer


def get_func_fields(func: Callable, *, is_in_class) -> list[FieldIn]:
    signature = inspect.signature(func)
    hints = get_type_hints(func)
    fields = [
        FieldIn(
            name=arg.name,
            type_hint=hints.get(arg.name, Any),
            consumed_by=[],
        )
        for arg in signature.parameters.values()
    ]
    if is_in_class:
        del fields[0]
    return fields


def get_result_type(func: Callable) -> Any:
    hints = get_type_hints(func)
    return hints.get("return", Any)


def make_method_spec(
    func: Callable,
    *,
    transformers: Sequence[RequestTransformer | ResponseTransformer],
    is_in_class: bool,
):
    fields_in = get_func_fields(func, is_in_class=is_in_class)
    fields_out = []
    request_transformers = [
        r for r in transformers if isinstance(r, RequestTransformer)
    ]
    for r in request_transformers:
        fields_out.extend(r.transform_fields(fields_in))

    return MethodSpec(
        func=func,
        name=func.__name__,
        doc=func.__doc__,
        fields_in=fields_in,
        fields_out=fields_out,
        result_type=get_result_type(func),
        request_transformers=request_transformers,
        response_transformers=[
            r for r in transformers if isinstance(r, ResponseTransformer)
        ],
    )
