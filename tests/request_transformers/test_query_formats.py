import pytest

from descanso.request import FieldIn, HttpRequest
from descanso.request_transformers import (
    DeepObjectQuery,
    DelimiterQuery,
    FormQuery,
    PhpStyleQuery,
)
from tests.request_transformers.utills import consumed_fields


@pytest.fixture
def fields_in():
    return [FieldIn("x", int)]


@pytest.mark.parametrize(
    ("transformer", "expected_params"),
    [
        (DeepObjectQuery(), [("x[]", "1"), ("x[]", "2")]),
        (FormQuery(), [("x", "1"), ("x", "2")]),
        (DelimiterQuery(), [("x", "1,2")]),
        (DelimiterQuery("|"), [("x", "1|2")]),
    ],
)
def test_list(transformer, expected_params, fields_in):
    assert str(transformer)
    assert transformer.transform_fields(fields_in) == []
    assert consumed_fields(fields_in, transformer) == []
    request = HttpRequest(
        query_params=[
            ("x", [1, 2]),
        ],
    )
    request = transformer.transform_request(request, fields_in, [], {"x": 1})
    assert request == HttpRequest(query_params=expected_params)


@pytest.mark.parametrize(
    ("transformer", "expected_params"),
    [
        (DeepObjectQuery(), [("x[a]", "1"), ("x[b]", "2")]),
        (FormQuery(), [("a", "1"), ("b", "2")]),
        (DelimiterQuery(), [("x", "a,1,b,2")]),
        (DelimiterQuery("|"), [("x", "a|1|b|2")]),
    ],
)
def test_dict(transformer, expected_params, fields_in):
    assert str(transformer)
    assert transformer.transform_fields(fields_in) == []
    assert consumed_fields(fields_in, transformer) == []
    request = HttpRequest(
        query_params=[
            ("x", {"a": 1, "b": 2, "c": None}),
        ],
    )
    request = transformer.transform_request(request, fields_in, [], {"x": 1})
    assert request == HttpRequest(query_params=expected_params)


def test_nested_php_style(fields_in):
    transformer = PhpStyleQuery()
    assert str(transformer)
    assert transformer.transform_fields(fields_in) == []
    assert consumed_fields(fields_in, transformer) == []
    request = HttpRequest(
        query_params=[
            (
                "x",
                {
                    "a": 1,
                    "b": [
                        {"a": 2, "b": 3},
                        {"a": 4, "b": 5},
                    ],
                    "c": None,
                },
            ),
        ],
    )
    expected_params = [
        ("x[a]", "1"),
        ("x[b][0][a]", "2"),
        ("x[b][0][b]", "3"),
        ("x[b][1][a]", "4"),
        ("x[b][1][b]", "5"),
    ]
    request = transformer.transform_request(request, fields_in, [], {"x": 1})
    assert request == HttpRequest(query_params=expected_params)
