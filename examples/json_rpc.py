import logging
from dataclasses import dataclass
from typing import Any
from uuid import uuid4

from adaptix import NameStyle, Retort, name_mapping
from requests import Session

from descanso.http.requests import RequestsClient
from descanso.method_descriptor import MethodBinder
from descanso.request import (
    Field,
    FieldDestintation,
    HttpRequest,
    RequestTransformer,
)
from descanso.request_transformers import Body, JsonDump, Method, RetortDump
from descanso.response import HttpResponse, ResponseTransformer
from descanso.response_transofrmers import (
    ErrorRaiser,
    JsonLoad,
    KeepResponse,
    RetortLoad,
)
from descanso.signature import make_method_spec

DEFAULT_BODY_PARAM = "body"


class PackJsonRPC(RequestTransformer):
    def  __init__(self, method: str) -> None:
        self.method = method

    def transform_request(
        self,
        request: HttpRequest,
        fields: list[Field],
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
        body_name = next(
            (field.name is FieldDestintation.BODY for field in spec.fields),
            None,
        )

        for field in spec.fields:
            if field.dest is not FieldDestintation.UNDEFINED:
                continue
            if not body_name and field.name == DEFAULT_BODY_PARAM:
                spec.request_transformers.append(Body(field.name))
        hint = next(
            (field.type_hint for field in spec.fields if field.name == body_name),
            Any,
        )
        spec.request_transformers.append(RetortDump(hint))
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
            spec.response_transformers.append(RetortLoad(spec.result_type))
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
        retort = Retort(
            strict_coercion=False,
            recipe=[
                name_mapping(name_style=NameStyle.CAMEL),
            ],
        )
        super().__init__(
            base_url="https://eth.merkle.io/",
            session=Session(),
            request_body_dumper=retort,
            request_params_dumper=Retort(),
            response_body_loader=retort,
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
