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
    """A complete token resolves to the caller and the tenant."""
    _stub_claims(
        {
            "sub": "7f1c0f2e",
            "name": "Koki Ueno",
            "custom:role": "owner",
            "cognito:groups": ["grp_sushi_taro"],
        },
        monkeypatch,
    )
    request = _request(authorization="Bearer dummy")

    caller = await get_authenticated_user(request)

    assert caller.user.user_id == "7f1c0f2e"
    assert caller.user.role is UserRole.OWNER
    assert caller.group_id == "grp_sushi_taro"
    assert request.state.authenticated_user is caller


@pytest.mark.asyncio
async def test_refuses_a_request_without_a_token():
    """No header means no identity, so the caller is unauthenticated."""
    with pytest.raises(HTTPException) as raised:
        await get_authenticated_user(_request())

    assert raised.value.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio
async def test_refuses_a_token_that_does_not_verify(monkeypatch):
    """An expired or forged token is unauthenticated, not forbidden."""

    async def _reject(_request: Request) -> dict[str, object]:
        raise ClientPermissionError("Token signature has expired.")

    monkeypatch.setattr(auth, "decode_token", _reject)

    with pytest.raises(HTTPException) as raised:
        await get_authenticated_user(_request(authorization="Bearer x"))

    assert raised.value.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio
async def test_refuses_a_genuine_token_with_no_role(monkeypatch):
    """The token is real, so the account is forbidden, not unknown."""
    _stub_claims(
        {
            "sub": "7f1c0f2e",
            "name": "Koki Ueno",
            "cognito:groups": ["grp_sushi_taro"],
        },
        monkeypatch,
    )

    with pytest.raises(HTTPException) as raised:
        await get_authenticated_user(_request(authorization="Bearer x"))

    assert raised.value.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.asyncio
async def test_refuses_a_user_of_two_groups(monkeypatch):
    """Serving one of two tenants would be the server guessing."""
    _stub_claims(
        {
            "sub": "7f1c0f2e",
            "name": "Koki Ueno",
            "custom:role": "owner",
            "cognito:groups": ["grp_sushi_taro", "grp_hotel_umi"],
        },
        monkeypatch,
    )

    with pytest.raises(HTTPException) as raised:
        await get_authenticated_user(_request(authorization="Bearer x"))

    assert raised.value.status_code == status.HTTP_403_FORBIDDEN
