from io import BytesIO

from dirty_equals import IsPartialDataclass
from kiss_headers import Header, Headers

from descanso.request import FileData, HttpRequest
from descanso.response import HttpResponse


class HasHeaders:
    def __init__(self, *headers: Header) -> None:
        self.orig = headers
        self.headers = headers
        self.headers: dict[str, Header | list[Header]] = {}
        for header in headers:
            if header.name in self.headers:
                old = self.headers[header.name]
                if isinstance(old, list):
                    old.append(header)
                else:
                    self.headers[header.name] = [old, header]
            else:
                self.headers[header.name] = header

    def __eq__(self, other: HttpResponse):
        for name, value in self.headers.items():
            assert other.headers.get(name) == value
        return True


def req_resp():
    return [
        (
            HttpRequest(
                url="/query_xxy",
                query_params=[
                    ("x", 1),
                    ("x", 2),
                    ("y", 3),
                ],
            ),
            IsPartialDataclass(
                status_code=200,
                body=b"ok",
            ),
        ),
        (
            HttpRequest(
                url="/conflict",
            ),
            IsPartialDataclass(
                status_code=409,
                status_text="test_conflict",
                body=b"test_conflict_body",
            ),
        ),
        (
            HttpRequest(
                url="/delete",
                method="DELETE",
            ),
            IsPartialDataclass(
                status_code=204,
            ),
        ),
        (
            HttpRequest(
                url="/headers",
                method="GET",
                headers=Headers(
                    Header("X-Test", "1"),
                ),
            ),
            HasHeaders(
                Header("X-Test", "2"),
                Header("X-Test", "3"),
                Header("Another", "value"),
            ),
        ),
        (
            HttpRequest(
                url="/files",
                files=[
                    ("x1", FileData(BytesIO(b"1"), filename="x1")),
                    ("x2", FileData(b"2", filename="x2")),
                    (
                        "x3",
                        FileData(
                            b"3",
                            filename="z3",
                            content_type="test_content_type",
                        ),
                    ),
                ],
                method="POST",
            ),
            IsPartialDataclass(
                status_code=200,
            ),
        ),
        (
            HttpRequest(
                url="/form",
                method="POST",
                body={
                    "field1": "1",
                    "field2": "2",
                },
            ),
            IsPartialDataclass(
                status_code=200,
            ),
        ),
    ]
