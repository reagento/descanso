from typing import Any

from descanso import Loader
from descanso.request import HttpRequest
from descanso.response import HttpResponse
from descanso.response_transformers import (
    BodyModelLoad,
    JsonLoad,
    KeepResponse,
)


def test_keep_response():
    json_load = KeepResponse(need_body=True)
    response = HttpResponse(
        status_code=200,
        status_text="OK",
        body='{"x": 1}',
    )
    response2 = json_load.transform_response(HttpRequest(), response)
    assert str(json_load)
    assert response2 == HttpResponse(
        status_code=200,
        status_text="OK",
        body=response,
    )


def test_json_load():
    json_load = JsonLoad()
    response = HttpResponse(
        status_code=200,
        status_text="OK",
        body='{"x": 1}',
    )
    response = json_load.transform_response(HttpRequest(), response)
    assert str(json_load)
    assert response == HttpResponse(
        status_code=200,
        status_text="OK",
        body={"x": 1},
    )


class Model:
    pass


class StubLoader(Loader):
    def load(self, data: Any, class_: Any) -> Any:
        return ["stub", data, class_]


def test_model_load():
    model_load = BodyModelLoad(
        type_hint=Model,
        loader=StubLoader(),
    )
    response = HttpResponse(
        status_code=200,
        status_text="OK",
        body="x",
    )
    response = model_load.transform_response(HttpRequest(), response)
    assert str(model_load)
    assert response == HttpResponse(
        status_code=200,
        status_text="OK",
        body=["stub", "x", Model],
    )
