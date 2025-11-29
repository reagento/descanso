from descanso import JsonRPCBuilder
from descanso.jsonrpc import (
    JsonRPCErrorRaiser,
    JsonRPCIdGenerator,
    JsonRPCMethod,
    PackJsonRPC,
    UnpackJsonRPC,
)
from descanso.request_transformers import (
    Body,
    BodyModelDump,
    JsonDump,
    Method,
    Skip,
    Url,
)
from descanso.response_transformers import BodyModelLoad, ErrorRaiser, JsonLoad
from .test_rest import StubConverter
from .utils import dirty


class Model:
    pass


def test_url():
    jsonrpc = JsonRPCBuilder(url="/foo")

    class Api:
        @jsonrpc("methodname")
        def do(self, body: int) -> Model:
            """Hello"""

    assert Api.do.spec.name == "do"
    assert Api.do.spec.doc == "Hello"
    assert Api.do.spec.request_transformers == [
        dirty[JsonRPCMethod](method="methodname"),
        dirty[Body](arg="body"),
        dirty[JsonRPCIdGenerator](id_generator=None),
        dirty[Url](original_template="/foo"),
        dirty[PackJsonRPC](),
        dirty[JsonDump](),
        dirty[Method](method="POST"),
    ]
    assert Api.do.spec.response_transformers == [
        dirty[ErrorRaiser](),
        dirty[JsonLoad](),
        dirty[JsonRPCErrorRaiser](),
        dirty[UnpackJsonRPC](),
    ]


def id_generator():
    return ""


def test_params():
    req_additional = Skip("0")
    resp_additional = ErrorRaiser(codes=[200])
    request_body_dumper = StubConverter()
    response_body_loader = StubConverter()
    request_body_post_dump = Skip("2")
    error_raiser = ErrorRaiser(codes=[400])
    response_body_pre_load = ErrorRaiser(codes=[500])
    json_rpc_error_raiser = JsonRPCErrorRaiser()

    jsonrpc = JsonRPCBuilder(
        req_additional,
        resp_additional,
        http_method="GET",
        id_generator=id_generator,
        request_body_dumper=request_body_dumper,
        response_body_loader=response_body_loader,
        request_body_post_dump=request_body_post_dump,
        error_raiser=error_raiser,
        json_rpc_error_raiser=json_rpc_error_raiser,
        response_body_pre_load=response_body_pre_load,
    )

    class Api:
        @jsonrpc("methodname")
        def do(self, data: int) -> Model:
            """Hello"""

    assert Api.do.spec.name == "do"
    assert Api.do.spec.doc == "Hello"
    assert Api.do.spec.request_transformers == [
        dirty[JsonRPCMethod](method="methodname"),
        req_additional,
        dirty[Body](arg="data"),
        dirty[BodyModelDump](dumper=request_body_dumper),
        dirty[JsonRPCIdGenerator](id_generator=id_generator),
        dirty[Url](original_template=""),
        dirty[PackJsonRPC](),
        request_body_post_dump,
        dirty[Method](method="GET"),
    ]
    assert Api.do.spec.response_transformers == [
        resp_additional,
        error_raiser,
        response_body_pre_load,
        json_rpc_error_raiser,
        dirty[UnpackJsonRPC](),
        dirty[BodyModelLoad](type_hint=Model, loader=response_body_loader),
    ]


def test_override():
    jsonrpc = JsonRPCBuilder(url="/foo")

    class Api:
        @jsonrpc("methodname", url="/bar")
        def do(self, data: int) -> Model:
            """Hello"""

    assert Api.do.spec.name == "do"
    assert Api.do.spec.doc == "Hello"
    assert Api.do.spec.request_transformers == [
        dirty[JsonRPCMethod](method="methodname"),
        dirty[Body](arg="data"),
        dirty[JsonRPCIdGenerator](id_generator=None),
        dirty[Url](original_template="/bar"),
        dirty[PackJsonRPC](),
        dirty[JsonDump](),
        dirty[Method](method="POST"),
    ]
    assert Api.do.spec.response_transformers == [
        dirty[ErrorRaiser](),
        dirty[JsonLoad](),
        dirty[JsonRPCErrorRaiser](),
        dirty[UnpackJsonRPC](),
    ]
