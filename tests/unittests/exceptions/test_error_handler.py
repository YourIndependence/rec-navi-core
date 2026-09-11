import json
from types import SimpleNamespace

import pytest

from recnavi.exceptions.error_handler import custom_exception_handler
from recnavi.exceptions.error_handler import logger
from recnavi.exceptions.exceptions import BaseClientExceptionError
from recnavi.exceptions.exceptions import ClientAuthorizationError


def make_request(
    *,
    body: bytes = b"",
    x_user: object | None = None,
    endpoint_name: str | None = "target_endpoint",
) -> SimpleNamespace:
    endpoint = (
        SimpleNamespace(__name__=endpoint_name)
        if endpoint_name is not None
        else None
    )
    return SimpleNamespace(
        state=SimpleNamespace(body=body, x_user=x_user),
        scope={"endpoint": endpoint},
    )


def response_content(response) -> dict[str, str]:
    return json.loads(response.body)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("exception", "status_code", "message"),
    [
        (ClientAuthorizationError("forbidden"), 403, "forbidden"),
        (BaseClientExceptionError("bad request"), 400, "bad request"),
        (TypeError("invalid type"), 400, "Invalid request parameter"),
        (RuntimeError("unexpected"), 500, "Unexpected Server Error"),
    ],
)
async def test_custom_exception_handler_returns_common_error_response(
    mocker,
    exception,
    status_code,
    message,
):
    request = make_request(body=b'{"query": "hello"}', x_user="user-1")
    mocker.patch.object(logger, "error")
    discord_mock = mocker.patch(
        "recnavi.exceptions.error_handler.post_error_discord",
    )

    response = await custom_exception_handler(request, exception)

    assert response.status_code == status_code
    assert response_content(response) == {
        "status": "error",
        "message": message,
    }
    if status_code == 500:
        discord_mock.assert_called_once()
    else:
        discord_mock.assert_not_called()


@pytest.mark.asyncio
async def test_custom_exception_handler_notifies_discord_with_request_context(
    mocker,
):
    request = make_request(
        body=b'{"query": "hello", "count": 2}',
        x_user={"id": "user-1"},
        endpoint_name="create_item",
    )
    exception = RuntimeError("database unavailable")
    mocker.patch.object(logger, "error")
    discord_mock = mocker.patch(
        "recnavi.exceptions.error_handler.post_error_discord",
    )

    await custom_exception_handler(request, exception)

    discord_mock.assert_called_once_with(
        function_name="create_item",
        e=exception,
        kwargs={
            "query": "hello",
            "count": 2,
            "x_user": {"id": "user-1"},
        },
        env=mocker.ANY,
        additional_message=mocker.ANY,
    )


@pytest.mark.asyncio
async def test_custom_exception_handler_uses_empty_kwargs_for_empty_body():
    request = make_request(x_user=None)

    response = await custom_exception_handler(
        request,
        BaseClientExceptionError("bad request"),
    )

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_custom_exception_handler_reports_body_parse_error(mocker):
    request = make_request(body=b"not-json")
    mocker.patch.object(logger, "error")
    discord_mock = mocker.patch(
        "recnavi.exceptions.error_handler.post_error_discord",
    )

    await custom_exception_handler(request, RuntimeError("unexpected"))

    kwargs = discord_mock.call_args.kwargs["kwargs"]
    assert kwargs["readRequestBodyError"] == "JSONDecodeError"
    assert kwargs["x_user"] is None


@pytest.mark.asyncio
async def test_custom_exception_handler_uses_unknown_for_missing_endpoint(
    mocker,
):
    request = make_request(endpoint_name=None)
    mocker.patch.object(logger, "error")
    discord_mock = mocker.patch(
        "recnavi.exceptions.error_handler.post_error_discord",
    )

    await custom_exception_handler(request, RuntimeError("unexpected"))

    assert discord_mock.call_args.kwargs["function_name"] == "unknown"
