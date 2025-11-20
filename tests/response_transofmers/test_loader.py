from typing import Any

from descanso import Loader
from descanso.response import HttpResponse
from descanso.response_transformers import BodyModelLoad, JsonLoad


def test_json_load():
    json_load = JsonLoad()
    response = HttpResponse(
        status_code=200,
        status_text="OK",
        body='{"x": 1}',
    )
    response = json_load.transform_response(response, {})
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
    response = model_load.transform_response(response, {})
    assert response == HttpResponse(
        status_code=200,
        status_text="OK",
        body=["stub", "x", Model],
    )
