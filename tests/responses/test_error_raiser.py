import pytest

from descanso.exceptions import ClientError, ServerError
from descanso.response import HttpResponse
from descanso.response_transformers import ErrorRaiser


def assert_client_error(
    error_raiser: ErrorRaiser,
    response: HttpResponse,
) -> None:
    with pytest.raises(ClientError) as exc_info:
        error_raiser.transform_response(response, {})

    exc = exc_info.value
    assert isinstance(exc, ClientError)
    assert exc.status_code == response.status_code
    assert exc.status_text == response.status_text


def test_ok() -> None:
    # Also checking that an empty list is interpreted as "not specified"
    error_raiser = ErrorRaiser(except_codes=[], codes=[])
    response = HttpResponse(status_code=200, status_text="ok")

    transformed_response = error_raiser.transform_response(response, {})

    assert transformed_response == response


def test_client_error() -> None:
    error_raiser = ErrorRaiser(except_codes=None, codes=None)
    response = HttpResponse(status_code=404, status_text="not_found")

    assert_client_error(error_raiser, response)


def test_server_error() -> None:
    error_raiser = ErrorRaiser(except_codes=[], codes=[])
    response = HttpResponse(status_code=502, status_text="bad_gateway")

    with pytest.raises(ServerError) as exc_info:
        error_raiser.transform_response(response, {})

    exc = exc_info.value
    assert isinstance(exc, ServerError)
    assert exc.status_code == response.status_code
    assert exc.status_text == response.status_text


@pytest.mark.parametrize(
    ("code", "good_status_code"),
    [
        (201, 200),
        (200, 404),
    ],
)
def test_codes(code: int, good_status_code: int) -> None:
    error_raiser = ErrorRaiser(codes=[code], except_codes=None)
    good_response = HttpResponse(
        status_code=good_status_code, status_text="ok",
    )
    bad_response = HttpResponse(status_code=code, status_text="created")

    transformed_good_response = error_raiser.transform_response(
        good_response,
        {},
    )

    assert_client_error(error_raiser, bad_response)
    assert transformed_good_response == good_response


@pytest.mark.parametrize(
    ("except_code", "bad_status_code"),
    [(201, 200), (404, 201)],
)
def test_except_codes(except_code: int, bad_status_code: int) -> None:
    error_raiser = ErrorRaiser(except_codes=[except_code])
    good_response = HttpResponse(
        status_code=except_code,
        status_text="created",
    )
    bad_response = HttpResponse(status_code=bad_status_code, status_text="ok")

    transformed_good_response = error_raiser.transform_response(
        good_response,
        {},
    )
    assert_client_error(error_raiser, bad_response)
    assert transformed_good_response == good_response


@pytest.mark.parametrize(
    ("except_codes", "except_codes_descriptions", "codes"),
    [
        (
            [200, 201, 202, 204],
            ["ok", "created", "accepted", "no_content"],
            [202, 204],
        ),
    ],
)
def test_except_codes_wider_than_codes(
    except_codes: list[int],
    except_codes_descriptions: list[str],
    codes: list[int],
) -> None:
    error_raiser = ErrorRaiser(except_codes=except_codes, codes=codes)

    bad_response = HttpResponse(status_code=302, status_text="found")
    assert_client_error(error_raiser, bad_response)

    for code, description in zip(
        except_codes,
        except_codes_descriptions,
        strict=True,
    ):
        response = HttpResponse(status_code=code, status_text=description)
        should_pass = (code in except_codes) and (code not in codes)

        if should_pass:
            transformed_response = error_raiser.transform_response(
                response,
                {},
            )
            assert transformed_response == response
            continue

        assert_client_error(error_raiser, response)


@pytest.mark.parametrize(
    ("except_codes", "except_codes_descriptions", "codes"),
    [
        (
            [202, 204],
            ["accepted", "no_content"],
            [200, 201, 202, 204],
        ),
    ],
)
def test_codes_wider_than_except_codes(
    except_codes: list[int],
    except_codes_descriptions: list[str],
    codes: list[int],
) -> None:
    error_raiser = ErrorRaiser(except_codes=except_codes, codes=codes)

    bad_response = HttpResponse(status_code=302, status_text="found")
    assert_client_error(error_raiser, bad_response)

    responses = [
        HttpResponse(code, desc)
        for code, desc in zip(
            except_codes,
            except_codes_descriptions,
            strict=True,
        )
    ]
    for response in responses:
        assert_client_error(error_raiser, response)
