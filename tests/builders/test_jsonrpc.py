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
    JsonDump,
    Method,
    Url,
)
from descanso.response_transformers import ErrorRaiser, JsonLoad
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


def test_body():
    jsonrpc = JsonRPCBuilder(body_name="data")

    class Api:
        @jsonrpc("methodname")
        def do(self, data: int) -> Model:
            """Hello"""

    assert Api.do.spec.name == "do"
    assert Api.do.spec.doc == "Hello"
    assert Api.do.spec.request_transformers == [
        dirty[JsonRPCMethod](method="methodname"),
        dirty[Body](arg="data"),
        dirty[JsonRPCIdGenerator](id_generator=None),
        dirty[Url](original_template=""),
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


def test_id_gen():
    jsonrpc = JsonRPCBuilder(id_generator=id_generator)

    class Api:
        @jsonrpc("methodname")
        def do(self) -> Model:
            """Hello"""

    assert Api.do.spec.name == "do"
    assert Api.do.spec.doc == "Hello"
    assert Api.do.spec.request_transformers == [
        dirty[JsonRPCMethod](method="methodname"),
        dirty[JsonRPCIdGenerator](id_generator=id_generator),
        dirty[Url](original_template=""),
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
