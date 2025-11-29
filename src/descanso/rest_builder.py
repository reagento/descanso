from collections.abc import Awaitable, Callable
from typing import (
    Any,
    Concatenate,
    ParamSpec,
    TypedDict,
    TypeVar,
    overload,
)

try:
    from typing import Unpack
except ImportError:
    T = TypeVar("T")
    Unpack = Any | T

from descanso import Dumper, Loader
from descanso.builder_base import (
    DEFAULT_BODY_PARAM,
    Decorator,
    Transformer,
    UrlSrc,
    url_transformer,
)
from descanso.method_descriptor import MethodBinder
from descanso.method_spec import MethodSpec
from descanso.request import FieldDestination, FieldOut, RequestTransformer
from descanso.request_transformers import (
    Body,
    BodyModelDump,
    FormQuery,
    JsonDump,
    Method,
    Query,
    QueryModelDump,
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


class BuilderParams(TypedDict):
    body_name: str

    query_param_dumper: Dumper | None
    request_body_dumper: Dumper | None
    request_body_post_dump: RequestTransformer | None
    query_param_post_dump: RequestTransformer | None

    response_body_loader: Loader | None
    response_body_pre_load: ResponseTransformer | None
    error_raiser: ResponseTransformer | None


class RestBuilder(Decorator):
    def __init__(
        self,
        *transformers: Transformer,
        **params: Unpack[BuilderParams],
    ) -> None:
        self.transformers = transformers
        self.params = params

    def with_params(
        self,
        *transformers: Transformer,
        **params: Unpack[BuilderParams],
    ) -> "RestBuilder":
        return RestBuilder(
            *transformers,
            *self.transformers,
            **(self.params | params),
        )

    def get(
        self,
        url: UrlSrc,
        *transformers: Transformer,
        **params: Unpack[BuilderParams],
    ) -> "RestBuilder":
        return self.with_params(
            url_transformer(url),
            Method("GET"),
            *transformers,
            **params,
        )

    def post(
        self,
        url: UrlSrc,
        *transformers: Transformer,
        **params: Unpack[BuilderParams],
    ) -> "RestBuilder":
        return self.with_params(
            url_transformer(url),
            Method("POST"),
            *transformers,
            **params,
        )

    def put(
        self,
        url: UrlSrc,
        *transformers: Transformer,
        **params: Unpack[BuilderParams],
    ) -> "RestBuilder":
        return self.with_params(
            url_transformer(url),
            Method("PUT"),
            *transformers,
            **params,
        )

    def patch(
        self,
        url: UrlSrc,
        *transformers: Transformer,
        **params: Unpack[BuilderParams],
    ) -> "RestBuilder":
        return self.with_params(
            url_transformer(url),
            Method("PATCH"),
            *transformers,
            **params,
        )

    def delete(
        self,
        url: UrlSrc,
        *transformers: Transformer,
        **params: Unpack[BuilderParams],
    ) -> "RestBuilder":
        return self.with_params(
            url_transformer(url),
            Method("DELETE"),
            *transformers,
            **params,
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

    def _add_default_request_body_transformers(self, spec: MethodSpec):
        default_body_name = self.params.get("body_name", DEFAULT_BODY_PARAM)

        body_out = self._get_body_field(spec)
        for field in spec.fields_in:
            if field.consumed_by:
                continue
            if not body_out and field.name == default_body_name:
                self._add_request_transformer(spec, Body(field.name))

        if self._get_body_field(spec):
            dumper = self.params.get("request_body_dumper")
            if dumper:
                self._add_request_transformer(spec, BodyModelDump(dumper))

            post_dump = self.params.get("request_body_post_dump", ...)
            if post_dump is ...:
                self._add_request_transformer(spec, JsonDump())
            elif post_dump:
                self._add_request_transformer(spec, post_dump)

    def _add_default_query_transformers(self, spec: MethodSpec):
        for field in spec.fields_in:
            if field.consumed_by:
                continue
            self._add_request_transformer(spec, Query(field.name))

        if dumper := self.params.get("query_param_dumper"):
            self._add_request_transformer(spec, QueryModelDump(dumper))
        query_post_dump = self.params.get("query_param_post_dump", ...)
        if query_post_dump is ...:
            self._add_request_transformer(spec, FormQuery())
        elif query_post_dump:
            self._add_request_transformer(spec, query_post_dump)
        return []

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

    def __call__(
        self,
        func: Callable[Concatenate[Any, _MethodParamSpec], _MethodResultT],
    ) -> MethodBinder[_MethodParamSpec, _MethodResultT]:
        spec = make_method_spec(
            func,
            transformers=self.transformers,
            is_in_class=True,
        )
        self._add_default_request_body_transformers(spec)
        self._add_default_query_transformers(spec)
        self._add_default_response_transformers(spec)
        return MethodBinder(spec)
