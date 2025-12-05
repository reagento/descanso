from descanso.jsonrpc import (
    EXTRA_JSON_RPC_METHOD,
    EXTRA_JSON_RPC_REQUEST_ID,
    PackJsonRPC,
)
from descanso.request import HttpRequest


def test_empty_body_omit_params() -> None:
    request = HttpRequest(
        extras=[
            (EXTRA_JSON_RPC_REQUEST_ID, "some_id"),
            (EXTRA_JSON_RPC_METHOD, "some_method"),
        ],
        method="POST",
    )
    expected_body = {
        "id": "some_id",
        "method": "some_method",
        "jsonrpc": "2.0",
    }

    transformer = PackJsonRPC()
    result_request = transformer.transform_request(request, [], [], {})

    assert result_request.body == expected_body


def test_body_set_in_params() -> None:
    params = {"param1": "value1", "param2": "value2"}
    request = HttpRequest(
        body=params,
        extras=[
            (EXTRA_JSON_RPC_REQUEST_ID, "some_id"),
            (EXTRA_JSON_RPC_METHOD, "some_method"),
        ],
        method="POST",
    )
    expected_body = {
        "id": "some_id",
        "method": "some_method",
        "jsonrpc": "2.0",
        "params": params,
    }

    transformer = PackJsonRPC()
    result_request = transformer.transform_request(request, [], [], {})

    assert result_request.body == expected_body
