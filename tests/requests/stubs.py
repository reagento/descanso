from dataclasses import asdict, is_dataclass
from typing import Any

import requests

from descanso import Dumper, Loader
from descanso.http.requests import RequestsClient


class StubConverter(Loader, Dumper):
    def load(self, data: Any, class_: Any) -> Any:
        return data

    def dump(self, data: Any, class_: Any) -> Any:
        if is_dataclass(class_):
            return asdict(data)
        return data


class StubRequestsClient(RequestsClient):
    def __init__(self, session: requests.Session):
        super().__init__(
            base_url="https://example.com",
            session=session,
            request_body_dumper=StubConverter(),
            response_body_loader=StubConverter(),
            request_params_dumper=StubConverter(),
        )
