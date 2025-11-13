import logging
from dataclasses import dataclass
from typing import Any, Sequence
from uuid import uuid4

from adaptix import NameStyle, Retort, name_mapping
from requests import Session

from descanso.http.requests import RequestsClient
from descanso.method_descriptor import MethodBinder
from descanso.method_spec import MethodSpec
from descanso.request import (
    FieldDestintation,
    HttpRequest,
    RequestTransformer, FieldIn, FieldOut,
)
from descanso.request_transformers import Body, JsonDump, Method, BodyModelDump
from descanso.response import HttpResponse, ResponseTransformer
from descanso.response_transofrmers import (
    ErrorRaiser,
    JsonLoad,
    KeepResponse,
    BodyModelLoad,
)
from descanso.signature import make_method_spec

DEFAULT_BODY_PARAM = "body"


class PackJsonRPC(RequestTransformer):
    def  __init__(self, method: str) -> None:
        self.method = method

    def transform_request(
        self,
        request: HttpRequest,
        fields_in: Sequence[FieldIn],
        fields_out: Sequence[FieldOut],
        data: dict[str, Any],
    ) -> HttpRequest:
        request.body = {
            "jsonrpc": "2.0",
            "id": str(uuid4()),
            "method": self.method,
            "params": request.body,
        }
        return request


class UnpackJsonRPC(ResponseTransformer):
    def need_response_body(self, response: HttpResponse) -> bool:
        return True

    def transform_response(
        self,
        response: HttpResponse,
        fields: dict[str, Any],
    ) -> HttpResponse:
        response.body = response.body.get("result")
        return response


class JsonRPCError(ResponseTransformer):
    def need_response_body(self, response: HttpResponse) -> bool:
        return True

    def transform_response(
        self,
        response: HttpResponse,
        fields: dict[str, Any],
    ) -> HttpResponse:
        if error := response.body.get("error"):
            raise ValueError(f"JSON RPC Error: {error}")
        return response


retort = Retort(
    strict_coercion=False,
    recipe=[
        name_mapping(name_style=NameStyle.CAMEL),
    ],
)


def _add_request_transformer(
        spec: MethodSpec,
        transformer: RequestTransformer,
):
    spec.request_transformers.append(transformer)
    spec.fields_out.extend(transformer.transform_fields(spec.fields_in))


def jsonrpc(
    method: str,
    *transformers: RequestTransformer | ResponseTransformer,
):
    def decorator(func):
        spec = make_method_spec(
            func,
            transformers=transformers,
            is_in_class=True,
        )
        body_out = next(
            (field for field in spec.fields_out if field.dest is FieldDestintation.BODY),
            None,
        )
        for field in spec.fields_in:
            if not body_out and field.name == DEFAULT_BODY_PARAM:
                _add_request_transformer(spec, Body(field.name))
        spec.request_transformers.append(BodyModelDump(retort))
        spec.request_transformers.append(PackJsonRPC(method))
        spec.request_transformers.append(Method("POST"))
        spec.request_transformers.append(JsonDump())

        spec.response_transformers.append(ErrorRaiser())
        spec.response_transformers.append(JsonLoad())
        spec.response_transformers.append(JsonRPCError())
        spec.response_transformers.append(UnpackJsonRPC())
        if spec.result_type is HttpResponse:
            spec.response_transformers.append(KeepResponse(need_body=False))
        elif spec.result_type is not Any and spec.result_type is not object:
            spec.response_transformers.append(BodyModelLoad(spec.result_type, loader=retort))
        return MethodBinder(spec)

    return decorator


# client
@dataclass
class Transaction:
    block_hash: str
    block_number: str
    from_: str
    chain_id: str
    transaction_index: str


class MyClient(RequestsClient):
    def __init__(self):
        super().__init__(
            base_url="https://eth.merkle.io/",
            session=Session(),
        )


    @jsonrpc("eth_getTransactionByHash")
    def get_transaction_by_hash(self, body: list[str]) -> Transaction:
        """Get transaction"""

    @jsonrpc("net_version")
    def net_version(self) -> str:
        """Retrieve net version"""

    @jsonrpc("eth_blockNumber")
    def eth_block_number(self) -> str:
        """Retrieve block number"""


logging.basicConfig(level=logging.INFO)
c = MyClient()
transaction = c.get_transaction_by_hash(
    ["0x05f71e1b2cb4f03e547739db15d080fd30c989eda04d37ce6264c5686e0722c9"],
)
print("Transaction: ", transaction)
print("Net version: ", c.net_version())
print("Block number:", c.eth_block_number())
