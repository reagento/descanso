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
    FieldDestination,
    HttpRequest,
    RequestTransformer, FieldIn, FieldOut,
)
from descanso.request_transformers import Body, JsonDump, Method, BodyModelDump
from descanso.response import HttpResponse, ResponseTransformer
from descanso.response_transformers import (
    ErrorRaiser,
    JsonLoad,
    KeepResponse,
    BodyModelLoad,
)
from descanso.signature import make_method_spec
from descanso.jsonrpc import JsonRPCBuilder

DEFAULT_BODY_PARAM = "body"



retort = Retort(
    strict_coercion=False,
    recipe=[
        name_mapping(name_style=NameStyle.CAMEL),
    ],
)

jsonrpc = JsonRPCBuilder(
    request_body_dumper=retort,
    response_body_loader=retort,
)


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
