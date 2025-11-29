import pytest

from descanso.exceptions import ClientError, HttpStatusError, ServerError
from descanso.request import HttpRequest
from descanso.response import HttpResponse
from descanso.response_transformers import ErrorRaiser


@pytest.mark.parametrize(
    ("status_code", "status_text", "except_codes", "codes"),
    [
        (200, "ok", None, None),
        (201, "created", [201], None),
        (
            204,
            "no_content",
            [200, 201, 202, 204],
            [202, 201, 200],
        ),
        (
            201,
            "created",
            [200, 201, 202, 204],
            [202, 204],
        ),
    ],
)
def test_ok(
    status_code: int,
    status_text: str,
    except_codes: list[int],
    codes: list[int],
):
    error_raiser = ErrorRaiser(except_codes=except_codes, codes=codes)
    response = HttpResponse(status_code=status_code, status_text=status_text)

    transformed_response = error_raiser.transform_response(
        HttpRequest(),
        response,
    )

    assert str(error_raiser)
    assert transformed_response == response


@pytest.mark.parametrize(
    ("status_code", "status_text", "except_codes", "codes", "error_type"),
    [
        # Client Error
        (404, "not_found", None, None, ClientError),
        (400, "bad_request", [], [], ClientError),
        (201, "created", None, [201], ClientError),
        (200, "ok", [201], None, ClientError),
        (302, "found", [200, 201, 202, 204], [202, 204], ClientError),
        (202, "accepted", [202, 204], [200, 201, 202, 204], ClientError),
        # Server Error
        (500, "internal_server_error", None, None, ServerError),
        (502, "bad_gateway", None, None, ServerError),
    ],
)
def test_error(
    status_code: int,
    status_text: str,
    except_codes: list[int],
    codes: list[int],
    error_type: type[HttpStatusError],
):
    error_raiser = ErrorRaiser(codes=codes, except_codes=except_codes)
    response = HttpResponse(status_code=status_code, status_text=status_text)

    with pytest.raises(error_type) as exc_info:
        error_raiser.transform_response(HttpRequest(), response)

    exc = exc_info.value
    assert str(error_raiser)
    assert isinstance(exc, error_type)
    assert exc.status_code == response.status_code
    assert exc.status_text == response.status_text
