# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Configuration and shared context for API tests.
Detected automatically by pytest, so no need to import it in the test code.
"""

import os
from collections.abc import Callable
from collections.abc import Iterator
from typing import cast

import pytest
from fastapi import FastAPI
from fastapi import Request
from fastapi.testclient import TestClient

from recnavi.apis.auth.auth import verify_user
from recnavi.config.variables import PROJECTS_TABLE_NAME
from recnavi.config.variables import SCENES_TABLE_NAME
from recnavi.config.variables import TEMPLATES_TABLE_NAME
from recnavi.config.variables import USERS_TABLE_NAME
from recnavi.core.database.base_database import BaseDatabase
from recnavi.core.types.user import User
from recnavi.core.types.user import UserRole
from recnavi.exceptions.exceptions import ClientPermissionError
from recnavi.main import app
from tests.mockups.mock_database import MockDatabase


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    """Skip tests requiring real AWS access in CI."""
    if os.getenv("ENV") != "CI":
        return

    skip_real_aws = pytest.mark.skip(reason="real AWS tests are skipped in CI")
    for item in items:
        if item.get_closest_marker("real_aws") is not None:
            item.add_marker(skip_real_aws)


@pytest.fixture(scope="session", autouse=True)
def client():
    """FastAPI test client with CI infrastructure and auth isolation."""
    app.dependency_overrides[verify_user] = mock_verify_user

    with TestClient(app, raise_server_exceptions=False) as client:
        mock_infrastracture_injection_when_ci(app)
        yield client

    app.dependency_overrides.clear()


def mock_infrastracture_injection_when_ci(app: FastAPI) -> None:
    """Inject in-memory infrastructure for integration tests running in CI."""
    if os.environ.get("ENV") != "CI":
        return

    app.state.database = {
        USERS_TABLE_NAME: MockDatabase(),
        PROJECTS_TABLE_NAME: MockDatabase(),
        SCENES_TABLE_NAME: MockDatabase(),
        TEMPLATES_TABLE_NAME: MockDatabase(),
    }


@pytest.fixture(scope="session")
def auth_headers():
    """Mock auth header"""
    token = "dummy_token"
    return {
        "Authorization": f"Bearer {token}",
        "Client-Id": "dummy_client_id",
    }


@pytest.fixture
def mock_x_user() -> User:
    return get_mock_x_user()


def get_mock_x_user() -> User:
    return User(
        user_id="test-user-123",
        user_name="Test User",
        role=UserRole.ADMIN,
        group_id="it-group",
    )


def mock_verify_user(request: Request) -> User:
    authorization = request.headers.get("authorization")
    if not authorization:
        raise ClientPermissionError("Authorization header is required.")
    if not authorization.startswith("Bearer "):
        raise ClientPermissionError(
            "Authorization header must start with 'Bearer '",
        )
    return get_mock_x_user()


@pytest.fixture
def databases() -> dict[str, BaseDatabase]:
    """In-memory tables injected in CI (skipped when real AWS is used)."""
    if os.environ.get("ENV") != "CI":
        pytest.skip("success-path tests need the in-memory tables (ENV=CI)")
    return cast(dict[str, BaseDatabase], app.state.database)


@pytest.fixture
def as_user() -> Iterator[Callable[..., User]]:
    """Return a factory that makes requests run as the given user.

    The dependency override is restored after each test, so no real
    Cognito is touched and tests cannot leak a role into one another.
    """

    def _as_user(
        role: UserRole,
        group_id: str = "it-group",
        user_id: str = "test-user-123",
    ) -> User:
        user = User(
            user_id=user_id,
            user_name=f"{role.value} {user_id}",
            role=role,
            group_id=group_id,
        )

        def _verify_user(request: Request) -> User:
            mock_verify_user(request)  # keeps the header checks
            return user

        app.dependency_overrides[verify_user] = _verify_user
        return user

    try:
        yield _as_user
    finally:
        app.dependency_overrides[verify_user] = mock_verify_user
