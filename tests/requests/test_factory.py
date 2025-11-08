from dataclasses import dataclass
from enum import Enum

import requests_mock
from adaptix import NameStyle, Retort, dumper, name_mapping

from descanso import patch
from descanso.http.requests import RequestsClient


class Selection(Enum):
    ONE = "ONE"
    TWO = "TWO"


@dataclass
class RequestBody:
    int_param: int
    selection: Selection


@dataclass
class ResponseBody:
    int_param: int
    selection: Selection


class Api(RequestsClient):
    def __init__(self, session):
        super().__init__(
            base_url="http://example.com/",
            session=session,
            request_body_dumper=Retort(
                recipe=[
                    name_mapping(name_style=NameStyle.CAMEL),
                ],
            ),
            request_params_dumper=Retort(
                recipe=[
                    dumper(str, lambda x: f"1{x}"),
                ],
            ),
            response_body_loader=Retort(
                recipe=[
                    name_mapping(name_style=NameStyle.LOWER_KEBAB),
                ],
            ),
        )

    @patch("/post/")
    def post_x(self, long_param: str, body: RequestBody) -> ResponseBody:
        raise NotImplementedError


def test_body(session, mocker: requests_mock.Mocker):
    mocker.patch(
        url="http://example.com/post/?long_param=1hello",
        text="""{"int-param": 1, "selection": "TWO"}""",
        complete_qs=True,
    )
    client = Api(session)
    result = client.post_x(
        long_param="hello",
        body=RequestBody(int_param=42, selection=Selection.ONE),
    )
    assert result == ResponseBody(int_param=1, selection=Selection.TWO)
    assert mocker.called_once

    resp = mocker.request_history[0].json()
    assert resp == {"intParam": 42, "selection": "ONE"}
