from io import BytesIO

from dirty_equals import IsPartialDataclass

from descanso.request import FileData, HttpRequest


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
