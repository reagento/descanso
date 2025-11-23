from contextlib import AbstractContextManager
from typing import Any
from unittest.mock import Mock

from dirty_equals import Contains, DirtyEquals, HasAttributes, IsInstance

from descanso import Loader, RestBuilder
from descanso.client import Dumper, SyncClient, SyncResponseWrapper
from descanso.request import HttpRequest
from descanso.request_transformers import (
    Body,
    BodyModelDump,
    FormQuery,
    JsonDump,
    Method,
    Query,
    QueryModelDump,
    Skip,
    Url,
)
from descanso.response_transformers import BodyModelLoad, ErrorRaiser, JsonLoad


class _Dirty:
    def __getitem__(self, item: type):
        def check(**attrs) -> DirtyEquals:
            return IsInstance(item) & HasAttributes(**attrs)

        return check


dirty = _Dirty()


class MockClient(SyncClient):
    def __init__(self, mock: Mock) -> None:
        self._mock = mock

    def send_request(
        self,
        request: HttpRequest,
    ) -> AbstractContextManager[SyncResponseWrapper]:
        return self._mock(request)


class Model:
    pass


def test_get_with_query():
    rest = RestBuilder()

    class Api:
        @rest.get("/foo")
        def do_get(self, x: int) -> Model:
            """Hello"""

    assert Api.do_get.name == "do_get"
    assert Api.do_get.doc == "Hello"
    assert Api.do_get.request_transformers == [
        dirty[Url](original_template="/foo"),
        dirty[Method](method="GET"),
        dirty[Query](name_out="x", original_template=None),
        dirty[FormQuery](),
    ]
    assert Api.do_get.response_transformers == [
        dirty[ErrorRaiser](),
        dirty[JsonLoad](),
    ]


def test_post_with_url_body():
    rest = RestBuilder()

    class Api:
        @rest.post("/foo{x}")
        def do_post(self, x: int, body: str) -> Model:
            """Hello"""

    assert Api.do_post.request_transformers == [
        dirty[Url](original_template="/foo{x}"),
        dirty[Method](method="POST"),
        dirty[Body](arg="body"),
        dirty[JsonDump](),
        dirty[FormQuery](),
    ]
    assert Api.do_post.response_transformers == [
        dirty[ErrorRaiser](),
        dirty[JsonLoad](),
    ]


def test_methods():
    rest = RestBuilder()

    class Api:
        @rest.get("/")
        def do_get(self) -> None: ...

        @rest.post("/")
        def do_post(self) -> None: ...

        @rest.delete("/")
        def do_delete(self) -> None: ...

        @rest.put("/")
        def do_put(self) -> None: ...

        @rest.patch("/")
        def do_patch(self) -> None: ...

    assert Api.do_get.request_transformers == Contains(
        dirty[Method](method="GET"),
    )
    assert Api.do_post.request_transformers == Contains(
        dirty[Method](method="POST"),
    )
    assert Api.do_delete.request_transformers == Contains(
        dirty[Method](method="DELETE"),
    )
    assert Api.do_put.request_transformers == Contains(
        dirty[Method](method="PUT"),
    )
    assert Api.do_patch.request_transformers == Contains(
        dirty[Method](method="PATCH"),
    )


class StubConverter(Dumper, Loader):
    def dump(self, data: Any, class_: Any) -> Any: ...

    def load(self, data: Any, class_: Any) -> Any: ...


def test_params():
    req_additional = Skip("0")
    resp_additional = ErrorRaiser(codes=[200])
    query_param_dumper = StubConverter()
    query_param_post_dump = Skip("1")
    request_body_dumper = StubConverter()
    response_body_loader = StubConverter()
    request_body_post_dump = Skip("2")
    error_raiser = ErrorRaiser(codes=[400])
    response_body_pre_load = ErrorRaiser(codes=[500])
    rest = RestBuilder(
        req_additional,
        resp_additional,
        query_param_dumper=query_param_dumper,
        query_param_post_dump=query_param_post_dump,
        request_body_dumper=request_body_dumper,
        response_body_loader=response_body_loader,
        request_body_post_dump=request_body_post_dump,
        body_name="x",
        error_raiser=error_raiser,
        response_body_pre_load=response_body_pre_load,
    )

    class Api:
        @rest.get("/")
        def do_get(self, x: int, body: str) -> Model: ...

    assert Api.do_get.request_transformers == [
        dirty[Url](original_template="/"),
        dirty[Method](method="GET"),
        req_additional,
        dirty[Body](arg="x"),
        dirty[BodyModelDump](dumper=request_body_dumper),
        request_body_post_dump,
        dirty[Query](name_out="body", original_template=None),
        dirty[QueryModelDump](dumper=query_param_dumper),
        query_param_post_dump,
    ]
    assert Api.do_get.response_transformers == [
        resp_additional,
        error_raiser,
        response_body_pre_load,
        dirty[BodyModelLoad](type_hint=Model, loader=response_body_loader),
    ]


def test_override_params():
    error_raiser = ErrorRaiser(codes=[400])
    response_body_pre_load = ErrorRaiser(codes=[500])
    response_body_pre_load2 = ErrorRaiser(codes=[502])
    rest = RestBuilder(
        error_raiser=error_raiser,
        response_body_pre_load=response_body_pre_load,
    )

    class Api:
        @rest.get("/", response_body_pre_load=response_body_pre_load2)
        def do_get(self, x: int, body: str) -> Model: ...

    assert Api.do_get.response_transformers == [
        error_raiser,
        response_body_pre_load2,
    ]
