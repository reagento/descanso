from collections.abc import Awaitable, Callable, Sequence
from typing import (
    Any,
    Concatenate,
    ParamSpec,
    Protocol,
    TypedDict,
    TypeVar,
    overload,
)
from uuid import uuid4

try:
    from typing import Unpack
except ImportError:
    T = TypeVar("T")
    Unpack = Any | T

from descanso import Dumper, Loader
from descanso.builder_base import (
    Transformer,
    UrlSrc,
    url_transformer,
)
from descanso.method_descriptor import MethodBinder
from descanso.method_spec import MethodSpec
from descanso.request import (
    FieldDestination,
    FieldIn,
    FieldOut,
    HttpRequest,
    RequestTransformer,
)
from descanso.request_transformers import (
    Body,
    BodyModelDump,
    JsonDump,
    Method,
)
from descanso.response import HttpResponse, ResponseTransformer
from descanso.response_transformers import (
    BodyModelLoad,
    ErrorRaiser,
    JsonLoad,
    KeepResponse,
)
from descanso.signature import make_method_spec

_MethodResultT = TypeVar("_MethodResultT")
_MethodParamSpec = ParamSpec("_MethodParamSpec")

EXTRA_JSON_RPC_REQUEST_ID = "JsonRPC.request_id"
EXTRA_JSON_RPC_METHOD = "JsonRPC.method"


def get_extra(request: HttpRequest, expected_key: str) -> Any:
    for key, value in request.extras:
        if key == expected_key:
            return value
    return None


class BaseJsonRPCError(Exception):
    pass


class MultipleBodyError(BaseJsonRPCError):
    def __init__(self, existing: str, new: str):
        self.existing = existing
        self.new = new

    def __str__(self):
        return (
            f"Cannot have multiple body fields, "
            f"found {self.existing}, {self.new}"
        )


class JsonRPCIdMismatchError(BaseJsonRPCError):
    pass


class JsonRPCError(BaseJsonRPCError):
    def __init__(self, code: int, message: str, data: Any) -> None:
        self.code = code
        self.message = message
        self.data = data

    def __repr__(self):
        return f"JsonRPCError({self.code}, {self.message!r}, {self.data!r})"


class IdGenerator(Protocol):
    def __call__(self) -> str: ...


class JsonRPCIdGenerator(RequestTransformer):
    def __init__(self, id_generator: IdGenerator | None = None) -> None:
        self.id_generator = id_generator

    def transform_fields(
        self,
        fields_in: Sequence[FieldIn],
    ) -> Sequence[FieldOut]:
        return [
            FieldOut(
                name=EXTRA_JSON_RPC_REQUEST_ID,
                dest=FieldDestination.EXTRA,
                type_hint=str,
            ),
        ]

    def _new_id(self) -> str:
        if not self.id_generator:
            return str(uuid4())
        return self.id_generator()

    def transform_request(
        self,
        request: HttpRequest,
        fields_in: Sequence[FieldIn],
        fields_out: Sequence[FieldOut],
        data: dict[str, Any],
    ) -> HttpRequest:
        request.extras.append((EXTRA_JSON_RPC_REQUEST_ID, self._new_id()))
        return request

    def __repr__(self):
        return f"{self.__class__.__name__}({self.id_generator})"


class JsonRPCMethod(RequestTransformer):
    def __init__(self, method: str):
        self.method = method

    def transform_fields(
        self,
        fields_in: Sequence[FieldIn],
    ) -> Sequence[FieldOut]:
        return [
            FieldOut(
                name=EXTRA_JSON_RPC_METHOD,
                dest=FieldDestination.EXTRA,
                type_hint=str,
            ),
        ]

    def transform_request(
        self,
        request: HttpRequest,
        fields_in: Sequence[FieldIn],
        fields_out: Sequence[FieldOut],
        data: dict[str, Any],
    ) -> HttpRequest:
        request.extras.append((EXTRA_JSON_RPC_METHOD, self.method))
        return request

    def __repr__(self):
        return f"{self.__class__.__name__}({self.method!r})"


class PackJsonRPC(RequestTransformer):
    def transform_fields(
        self,
        fields_in: Sequence[FieldIn],
    ) -> Sequence[FieldOut]:
        return []

    def transform_request(
        self,
        request: HttpRequest,
        fields_in: Sequence[FieldIn],
        fields_out: Sequence[FieldOut],
        data: dict[str, Any],
    ) -> HttpRequest:
        request_id = get_extra(request, EXTRA_JSON_RPC_REQUEST_ID)
        method = get_extra(request, EXTRA_JSON_RPC_METHOD)
        request.body = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": method,
            "params": request.body,
        }
        return request

    def __repr__(self):
        return f"{self.__class__.__name__}()"


class UnpackJsonRPC(ResponseTransformer):
    def need_response_body(self, response: HttpResponse) -> bool:
        return True

    def transform_response(
        self,
        request: HttpRequest,
        response: HttpResponse,
    ) -> HttpResponse:
        response.body = response.body.get("result")
        return response

    def __repr__(self):
        return f"{self.__class__.__name__}()"


class JsonRPCErrorRaiser(ResponseTransformer):
    def need_response_body(self, response: HttpResponse) -> bool:
        return True

    def transform_response(
        self,
        request: HttpRequest,
        response: HttpResponse,
    ) -> HttpResponse:
        request_id = get_extra(request, EXTRA_JSON_RPC_REQUEST_ID)
        if request_id != response.body.get("id"):
            raise JsonRPCIdMismatchError
        if error := response.body.get("error"):
            raise JsonRPCError(
                error["code"],
                error["message"],
                error.get("data"),
            )
        return response

    def __repr__(self):
        return f"{self.__class__.__name__}()"


class _BuilderParams(TypedDict, total=False):
    http_method: str
    url: UrlSrc
    id_generator: IdGenerator

    request_body_dumper: Dumper | None
    request_body_post_dump: RequestTransformer | None

    response_body_loader: Loader | None
    response_body_pre_load: ResponseTransformer | None
    error_raiser: ResponseTransformer | None
    json_rpc_error_raiser: ResponseTransformer | None


class JsonRPCBuilder:
    def __init__(
        self,
        *transformers: Transformer,
        **params: Unpack[_BuilderParams],
    ) -> None:
        self.transformers = transformers
        self.params = params

    def with_params(
        self,
        *transformers: Transformer,
        **params: Unpack[_BuilderParams],
    ) -> "JsonRPCBuilder":
        return JsonRPCBuilder(
            *transformers,
            *self.transformers,
            **(self.params | params),
        )

    def _add_request_transformer(
        self,
        spec: MethodSpec,
        transformer: RequestTransformer,
    ):
        spec.request_transformers.append(transformer)
        spec.fields_out.extend(transformer.transform_fields(spec.fields_in))

    def _get_body_field(self, spec: MethodSpec) -> FieldOut | None:
        for field in spec.fields_out:
            if field.dest is FieldDestination.BODY:
                return field
        return None

    def _add_body_transformer(self, spec: MethodSpec):
        body_out = self._get_body_field(spec)
        if body_out is None:
            body_name = None
        else:
            body_name = body_out.name
        for field in spec.fields_in:
            if field.consumed_by:
                continue
            if body_name:
                raise MultipleBodyError(body_name, field.name)
            body_name = field.name
            self._add_request_transformer(spec, Body(field.name))

    def _add_default_request_body_transformers(self, spec: MethodSpec):
        self._add_body_transformer(spec)

        if self._get_body_field(spec):
            dumper = self.params.get("request_body_dumper")
            if dumper:
                self._add_request_transformer(spec, BodyModelDump(dumper))

        id_generator = self.params.get("id_generator", ...)
        if id_generator is ...:
            self._add_request_transformer(spec, JsonRPCIdGenerator())
        elif id_generator:
            self._add_request_transformer(
                spec,
                JsonRPCIdGenerator(id_generator),
            )

        url_src = self.params.get("url") or ""
        self._add_request_transformer(spec, url_transformer(url_src))

        self._add_request_transformer(spec, PackJsonRPC())

        post_dump = self.params.get("request_body_post_dump", ...)
        if post_dump is ...:
            self._add_request_transformer(spec, JsonDump())
        elif post_dump:
            self._add_request_transformer(spec, post_dump)

        http_method = self.params.get("http_method", ...)
        if http_method is ...:
            self._add_request_transformer(spec, Method("POST"))
        elif http_method:
            self._add_request_transformer(spec, Method(http_method))

    def _add_default_response_transformers(self, spec: MethodSpec) -> None:
        error_raiser = self.params.get("error_raiser", ...)
        if error_raiser is ...:
            spec.response_transformers.append(ErrorRaiser())
        elif error_raiser:
            spec.response_transformers.append(error_raiser)

        pre_loader = self.params.get("response_body_pre_load", ...)
        if pre_loader is ...:
            spec.response_transformers.append(JsonLoad())
        elif pre_loader:
            spec.response_transformers.append(pre_loader)

        error_raiser = self.params.get("json_rpc_error_raiser", ...)
        if error_raiser is ...:
            spec.response_transformers.append(JsonRPCErrorRaiser())
        elif error_raiser:
            spec.response_transformers.append(error_raiser)

        spec.response_transformers.append(UnpackJsonRPC())

        loader = self.params.get("response_body_loader")
        if spec.result_type is HttpResponse:
            spec.response_transformers.append(KeepResponse(need_body=False))
        elif (
            loader
            and spec.result_type is not Any
            and spec.result_type is not object
        ):
            spec.response_transformers.append(
                BodyModelLoad(spec.result_type, loader=loader),
            )

    @overload
    def decorate(
        self,
        func: Callable[
            Concatenate[Any, _MethodParamSpec],
            Awaitable[_MethodResultT],
        ],
    ) -> MethodBinder[_MethodParamSpec, _MethodResultT]: ...

    @overload
    def decorate(
        self,
        func: Callable[Concatenate[Any, _MethodParamSpec], _MethodResultT],
    ) -> MethodBinder[_MethodParamSpec, _MethodResultT]: ...

    def decorate(
        self,
        func: Callable[Concatenate[Any, _MethodParamSpec], _MethodResultT],
    ) -> MethodBinder[_MethodParamSpec, _MethodResultT]:
        spec = make_method_spec(
            func,
            transformers=self.transformers,
            is_in_class=True,
        )
        self._add_default_request_body_transformers(spec)
        self._add_default_response_transformers(spec)
        return MethodBinder(spec)

    @overload
    def __call__(
        self,
        func: Callable[
            Concatenate[Any, _MethodParamSpec],
            Awaitable[_MethodResultT],
        ],
    ) -> MethodBinder[_MethodParamSpec, _MethodResultT]: ...

    @overload
    def __call__(
        self,
        func: Callable[Concatenate[Any, _MethodParamSpec], _MethodResultT],
    ) -> MethodBinder[_MethodParamSpec, _MethodResultT]: ...

    @overload
    def __call__(
        self,
        method: str,
        *transformers: Transformer,
        **params: Unpack[_BuilderParams],
    ) -> "JsonRPCBuilder": ...

    def __call__(
        self,
        func_or_method: str | Callable,
        *transformers: Transformer,
        **params: Unpack[_BuilderParams],
    ) -> Any:
        if transformers or params:
            instance = self.with_params(*transformers, **params)
        else:
            instance = self
        if isinstance(func_or_method, str):
            return instance.with_params(JsonRPCMethod(func_or_method))
        else:
            return instance.decorate(func_or_method)
