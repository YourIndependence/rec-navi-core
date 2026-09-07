# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Unit tests for the authenticated user dependency."""

import pytest
from fastapi import HTTPException
from fastapi import status
from starlette.requests import Request

from recnavi.apis.auth import auth
from recnavi.apis.auth.auth import get_authenticated_user
from recnavi.core.types.group_user import UserRole
from recnavi.exceptions.exceptions import ClientPermissionError
from tests.mockups.mock_user_repository import MockUserRepository


SIGNED_IN = "7f1c0f2e-0a3d-4a1b-9c2e-2b7a6d5e4f30"


def _request(*, authorization: str | None = None) -> Request:
    """A request carrying nothing but its authorization header."""
    headers = []
    if authorization is not None:
        headers.append((b"authorization", authorization.encode()))
    return Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/getMe",
            "headers": headers,
        },
    )


def _stub_claims(claims: dict[str, object], monkeypatch):
    """Answer the token verification with the given claims."""

    async def _decode(_request: Request) -> dict[str, object]:
        return claims

    monkeypatch.setattr(auth, "decode_token", _decode)


@pytest.mark.asyncio
async def test_returns_the_signed_in_user(monkeypatch):
    """The token names the user; the record says what they may do."""
    _stub_claims({"sub": SIGNED_IN}, monkeypatch)
    request = _request(authorization="Bearer dummy")

    user = await get_authenticated_user(request, MockUserRepository())

    assert user.user_id == SIGNED_IN
    assert user.user_name == "Koki Ueno"
    assert user.role is UserRole.OWNER
    assert user.group_id == "grp_sushi_taro"
    assert request.state.authenticated_user is user


@pytest.mark.asyncio
async def test_refuses_a_request_without_a_token():
    """No header means no identity, so the caller is unauthenticated."""
    with pytest.raises(HTTPException) as raised:
        await get_authenticated_user(_request(), MockUserRepository())

    assert raised.value.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio
async def test_refuses_a_token_that_does_not_verify(monkeypatch):
    """An expired or forged token is unauthenticated, not forbidden."""

    async def _reject(_request: Request) -> dict[str, object]:
        raise ClientPermissionError("Token signature has expired.")

    monkeypatch.setattr(auth, "decode_token", _reject)

    with pytest.raises(HTTPException) as raised:
        await get_authenticated_user(
            _request(authorization="Bearer x"),
            MockUserRepository(),
        )

    assert raised.value.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio
async def test_refuses_a_token_naming_nobody(monkeypatch):
    """A token with no sub cannot be turned into a user."""
    _stub_claims({}, monkeypatch)

    with pytest.raises(HTTPException) as raised:
        await get_authenticated_user(
            _request(authorization="Bearer x"),
            MockUserRepository(),
        )

    assert raised.value.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.asyncio
async def test_refuses_a_user_with_no_record(monkeypatch):
    """Signing up in Cognito does not by itself make an account usable.

    The token is genuine, so this is 403 and not 401: signing in again
    will not create the missing record.
    """
    _stub_claims({"sub": "nobody"}, monkeypatch)

    with pytest.raises(HTTPException) as raised:
        await get_authenticated_user(
            _request(authorization="Bearer x"),
            MockUserRepository(),
        )

    assert raised.value.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.asyncio
async def test_reads_the_record_rather_than_the_token(monkeypatch):
    """A role changed in the table takes effect without a new sign-in."""
    _stub_claims(
        {"sub": SIGNED_IN, "custom:role": "admin", "cognito:groups": ["x"]},
        monkeypatch,
    )

    user = await get_authenticated_user(
        _request(authorization="Bearer x"),
        MockUserRepository(),
    )

    assert user.role is UserRole.OWNER
    assert user.group_id == "grp_sushi_taro"
