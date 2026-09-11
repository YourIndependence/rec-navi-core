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

import pytest
from fastapi import Request
from fastapi.testclient import TestClient

from recnavi.apis.auth.auth import verify_user
from recnavi.core.types.user import User
from recnavi.exceptions.exceptions import ClientPermissionError
from recnavi.main import app


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
    """FastAPI test client with mocked authentication."""
    app.dependency_overrides[verify_user] = get_mock_x_user

    with TestClient(app, raise_server_exceptions=False) as client:
        yield client

    app.dependency_overrides.clear()


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


def get_mock_x_user(request: Request):
    authorization = request.headers.get("authorization")
    if not authorization:
        raise ClientPermissionError("Authorization header is required.")
    if not authorization.startswith("Bearer "):
        raise ClientPermissionError(
            "Authorization header must start with 'Bearer '",
        )
    return User(
        user_id="test-user-123",
        user_name="Test User",
        role="admin",
        group_id="group-999",
    )
