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
from fastapi import FastAPI
from fastapi import Request
from fastapi.testclient import TestClient

from recnavi.apis.auth.auth import verify_user
from recnavi.config.variables import MEDIA_BUCKET_NAME
from recnavi.config.variables import PROJECTS_TABLE_NAME
from recnavi.config.variables import SCENE_IMAGES_BUCKET_NAME
from recnavi.config.variables import SCENES_TABLE_NAME
from recnavi.config.variables import TEMPLATES_TABLE_NAME
from recnavi.config.variables import USERS_TABLE_NAME
from recnavi.core.types.user import User
from recnavi.core.types.user import UserRole
from recnavi.exceptions.exceptions import ClientPermissionError
from recnavi.main import app
from tests.mockups.mock_database import MockDatabase
from tests.mockups.mock_object_storage import MockObjectStorage


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

    app.dependency_overrides.pop(verify_user, None)


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
    app.state.object_storage = MockObjectStorage(
        bucket_name=MEDIA_BUCKET_NAME,
    )

    app.state.scene_images_storage = MockObjectStorage(
        bucket_name=SCENE_IMAGES_BUCKET_NAME,
    )


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
