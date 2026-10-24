# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""HTTP boundary tests for authentication dependencies."""

from collections.abc import Iterator
from unittest.mock import AsyncMock
from unittest.mock import patch

import pytest
from fastapi import FastAPI
from fastapi import Request
from fastapi import status
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient

from recnavi.apis.auth.auth import verify_user
from recnavi.config.variables import USERS_TABLE_NAME
from recnavi.core.types.user import User
from recnavi.core.types.user import UserRole
from recnavi.exceptions.exceptions import ClientPermissionError
from tests.mockups.mock_database import MockDatabase


@pytest.fixture(scope="module")
def auth_client() -> Iterator[TestClient]:
    """Expose the authentication dependency through a small HTTP route."""
    auth_app = FastAPI()

    @auth_app.exception_handler(ClientPermissionError)
    async def handle_permission_error(
        _request: Request,
        exception: ClientPermissionError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={"detail": str(exception)},
        )

    @auth_app.get("/protected")
    async def protected(request: Request) -> dict[str, str]:
        user = await verify_user(request)
        return {"userId": user.user_id}

    auth_app.state.database = {USERS_TABLE_NAME: MockDatabase()}
    with TestClient(auth_app) as test_client:
        yield test_client


def test_protected_route_rejects_missing_authorization_header(
    auth_client: TestClient,
) -> None:
    response = auth_client.get("/protected")

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json() == {"detail": "Authorization header is required."}


def test_protected_route_rejects_non_bearer_authorization_header(
    auth_client: TestClient,
) -> None:
    response = auth_client.get(
        "/protected",
        headers={"Authorization": "Basic token"},
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json() == {
        "detail": "Authorization header must start with 'Bearer '",
    }


def test_protected_route_resolves_user_from_decoded_token(
    auth_client: TestClient,
) -> None:
    user = User(
        user_id="user-123",
        user_name="Test User",
        role=UserRole.STAFF,
        group_id="group-456",
    )
    with (
        patch(
            "recnavi.apis.auth.auth.decode_token",
            new=AsyncMock(return_value={"sub": "user-123"}),
        ) as decode_token,
        patch(
            "recnavi.apis.auth.auth.get_user_by_id",
            new=AsyncMock(return_value=user),
        ) as get_user_by_id,
    ):
        response = auth_client.get(
            "/protected",
            headers={"Authorization": "Bearer signed-token"},
        )

    assert response.status_code == 200
    assert response.json() == {"userId": "user-123"}
    decode_token.assert_awaited_once()
    get_user_by_id.assert_awaited_once_with(
        user_id="user-123",
        user_database=auth_client.app.state.database[USERS_TABLE_NAME],
    )
