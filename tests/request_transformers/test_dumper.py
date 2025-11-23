from typing import Any

import pytest
from kiss_headers import Header, Headers

from descanso import Dumper
from descanso.request import (
    FieldDestination,
    FieldIn,
    FieldOut,
    HttpRequest,
    RequestTransformer,
)
from descanso.request_transformers import (
    BodyModelDump,
    JsonDump,
    QueryModelDump,
)
from tests.request_transformers.utills import consumed_fields


class QueryModel:
    pass


class BodyModel:
    pass


class StubDumper(Dumper):
    def dump(self, data: Any, class_: Any) -> Any:
        return ["stub", data, class_]


@pytest.fixture
def fields_in():
    return [FieldIn("x", int)]


@pytest.fixture
def fields_out():
    return [
        FieldOut(name="x", dest=FieldDestination.QUERY, type_hint=QueryModel),
        FieldOut(name=None, dest=FieldDestination.BODY, type_hint=BodyModel),
    ]


@pytest.fixture
def model_request():
    return HttpRequest(
        query_params=[
            ("x", "x_value"),
            ("y", "y_value"),
        ],
        body="body_value",
    )


@pytest.mark.parametrize(
    ("transformer", "expected_request"),
    [
        (
            QueryModelDump(StubDumper()),
            HttpRequest(
                query_params=[
                    ("x", ["stub", "x_value", QueryModel]),
                    ("y", ["stub", "y_value", Any]),
                ],
                body="body_value",
            ),
        ),
        (
            BodyModelDump(StubDumper()),
            HttpRequest(
                query_params=[
                    ("x", "x_value"),
                    ("y", "y_value"),
                ],
                body=["stub", "body_value", BodyModel],
            ),
        ),
    ],
)
def test_body_model_dump(
    fields_in,
    fields_out,
    model_request,
    transformer: RequestTransformer,
    expected_request: HttpRequest,
):
    assert transformer.transform_fields(fields_in) == []
    assert consumed_fields(fields_in, transformer) == []
    request = transformer.transform_request(
        model_request,
        fields_in,
        fields_out,
        {"x": 0, "y": 0},
    )
    assert request == expected_request


def test_body_json_dump(fields_in, fields_out):
    transformer = JsonDump()
    assert transformer.transform_fields(fields_in) == []
    assert consumed_fields(fields_in, transformer) == []
    request = transformer.transform_request(
        HttpRequest(body={"x": "value"}),
        fields_in,
        fields_out,
        {"x": 0, "y": 0},
    )
    assert request == HttpRequest(
        body='{"x": "value"}',
        headers=Headers(Header("Content-Type", "application/json")),
    )
