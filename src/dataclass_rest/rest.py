from typing import Any, Callable, Dict, Optional, TypeVar, cast

from .boundmethod import BoundMethod
from .method import Method
from .parse_func import DEFAULT_BODY_PARAM, UrlTemplate, parse_func
from .response_type import ResponseTypeLiteral, ResponseType

_Func = TypeVar("_Func", bound=Callable[..., Any])


def rest(
    url_template: UrlTemplate,
    *,
    method: str,
    body_name: str = DEFAULT_BODY_PARAM,
    additional_params: Optional[Dict[str, Any]] = None,
    method_class: Optional[Callable[..., BoundMethod]] = None,
    send_json: bool = True,
    response_type: ResponseTypeLiteral = "json",
) -> Callable[[Callable], Method]:
    if additional_params is None:
        additional_params = {}
    try:
        response_type_enum = ResponseType(response_type)
    except ValueError:
        raise TypeError(
            f"'{response_type}' is not a valid response type. "
            f"Use one of {list(ResponseTypeLiteral.__args__)}"
        )

    def dec(func: Callable) -> Method:
        method_spec = parse_func(
            func=func,
            body_param_name=body_name,
            url_template=url_template,
            method=method,
            additional_params=additional_params,
            is_json_request=send_json,
        )
        return Method(method_spec, method_class=method_class, response_type=response_type_enum)

    return dec


def _rest_method(func: _Func, method: str) -> _Func:
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs, method=method)

    return cast(_Func, wrapper)


get = _rest_method(rest, method="GET")
post = _rest_method(rest, method="POST")
put = _rest_method(rest, method="PUT")
patch = _rest_method(rest, method="PATCH")
delete = _rest_method(rest, method="DELETE")
