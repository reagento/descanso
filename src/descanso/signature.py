import inspect
from collections.abc import Callable, Sequence
from typing import Any, get_type_hints

from .methodspec import MethodSpec
from .request import Field, FieldDestintation, RequestTransformer
from .response import ResponseTransformer


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
            ),
        )
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
    return MethodSpec(
        func=func,
        name=func.__name__,
        doc=func.__doc__,
        fields=get_func_fields(func, is_in_class=is_in_class),
        result_type=get_result_type(func),
        request_transformers=[
            r for r in transformers if isinstance(r, RequestTransformer)
        ],
        response_transformers=[
            r for r in transformers if isinstance(r, ResponseTransformer)
        ],
    )
