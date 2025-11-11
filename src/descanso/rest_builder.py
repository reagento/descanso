from collections.abc import Awaitable, Callable
from typing import (
    Any,
    Concatenate,
    ParamSpec,
    Protocol,
    TypedDict,
    TypeVar,
    Unpack,
    overload,
)

from descanso import Dumper, Loader
from descanso.method_descriptor import MethodBinder
from descanso.method_spec import MethodSpec
from descanso.request import FieldDestintation, RequestTransformer
from descanso.request_transformers import (
    Body,
    JsonDump,
    Method,
    Query,
    RetortDump,
    Url,
)
from descanso.response import HttpResponse, ResponseTransformer
from descanso.response_transofrmers import (
    ErrorRaiser,
    JsonLoad,
    KeepResponse,
    RetortLoad,
)
from descanso.signature import make_method_spec

DEFAULT_BODY_PARAM = "body"

_MethodResultT = TypeVar("_MethodResultT")
_MethodParamSpec = ParamSpec("_MethodParamSpec")


class Decorator(Protocol):
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

    def __call__(self, *args, **kwargs):
        raise NotImplementedError


Transformer = RequestTransformer | ResponseTransformer
UrlSrc = str | Callable | Url


class _BuilderParams(TypedDict, total=False):
    body_name: str

    query_param_dumper: Dumper | None
    request_body_dumper: Dumper | None
    request_body_post_dump: RequestTransformer | None
    query_param_post_dump: RequestTransformer | None

    response_body_loader: Loader | None
    response_body_pre_load: ResponseTransformer | None
    error_raiser: ResponseTransformer | None


def _url_transformer(url: UrlSrc) -> Url:
    if isinstance(url, Url):
        return url
    return Url(url)


class RestBuilder(Decorator):
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
        **params: Unpack[_BuilderParams],
    ) -> "RestBuilder":
        return self.with_params(
            _url_transformer(url),
            Method("GET"),
            *transformers,
            **params,
        )

    def post(
        self,
        url: UrlSrc,
        *transformers: Transformer,
        **params: Unpack[_BuilderParams],
    ) -> "RestBuilder":
        return self.with_params(
            _url_transformer(url),
            Method("POST"),
            *transformers,
            **params,
        )

    def put(
        self,
        url: UrlSrc,
        *transformers: Transformer,
        **params: Unpack[_BuilderParams],
    ) -> "RestBuilder":
        return self.with_params(
            _url_transformer(url),
            Method("PUT"),
            *transformers,
            **params,
        )

    def patch(
        self,
        url: UrlSrc,
        *transformers: Transformer,
        **params: Unpack[_BuilderParams],
    ) -> "RestBuilder":
        return self.with_params(
            _url_transformer(url),
            Method("PATCH"),
            *transformers,
            **params,
        )

    def delete(
        self,
        url: UrlSrc,
        *transformers: Transformer,
        **params: Unpack[_BuilderParams],
    ) -> "RestBuilder":
        return self.with_params(
            _url_transformer(url),
            Method("DELETE"),
            *transformers,
            **params,
        )

    def _default_request_transformers(
        self,
        spec: MethodSpec,
    ) -> list[RequestTransformer]:
        transformers = []
        default_body_name = self.params.get("body_name", DEFAULT_BODY_PARAM)
        body_name = next(
            (field.name is FieldDestintation.BODY for field in spec.fields),
            None,
        )

        for field in spec.fields:
            if field.dest is not FieldDestintation.UNDEFINED:
                continue
            if not body_name and field.name == default_body_name:
                transformers.append(Body(field.name))
                body_name = default_body_name
            else:
                transformers.append(Query(field.name))
        if body_name:
            hint = next(
                (
                    field.type_hint
                    for field in spec.fields
                    if field.name == body_name
                ),
                Any,
            )

            dumper = self.params.get("request_body_dumper")
            if hint is not Any and dumper:
                transformers.append(RetortDump(hint, dumper))

            post_dump = self.params.get("request_body_post_dump", ...)
            if post_dump is ...:
                transformers.append(JsonDump())
            elif post_dump:
                transformers.append(post_dump)

        return []

    def _default_response_transformers(
        self,
        spec: MethodSpec,
    ) -> list[ResponseTransformer]:
        transformers = []
        error_raiser = self.params.get("error_raiser", ...)
        if error_raiser is ...:
            transformers.append(ErrorRaiser())
        elif error_raiser:
            transformers.append(error_raiser)

        pre_loader = self.params.get("response_body_pre_load", ...)
        if pre_loader is ...:
            transformers.append(JsonLoad())
        elif pre_loader:
            transformers.append(pre_loader)

        loader = self.params.get("response_body_loader")
        if spec.result_type is HttpResponse:
            transformers.append(KeepResponse(need_body=False))
        elif (
            loader
            and spec.result_type is not Any
            and spec.result_type is not object
        ):
            transformers.append(
                RetortLoad(spec.result_type, loader=loader),
            )
        return transformers

    def __call__(
        self,
        func: Callable[Concatenate[Any, _MethodParamSpec], _MethodResultT],
    ) -> MethodBinder[_MethodParamSpec, _MethodResultT]:
        spec = make_method_spec(
            func,
            transformers=self.transformers,
            is_in_class=True,
        )
        for transformer in spec.request_transformers:
            spec.fields = transformer.transform_fields(fields=spec.fields)
        spec.request_transformers.extend(
            self._default_request_transformers(spec),
        )
        spec.response_transformers.extend(
            self._default_response_transformers(spec),
        )
        return MethodBinder(spec)
