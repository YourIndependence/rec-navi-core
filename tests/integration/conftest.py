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

import pytest
from fastapi.testclient import TestClient

from recnavi.apis.auth.auth import get_authenticated_user
from recnavi.apis.auth.auth import verify_user
from recnavi.apis.dependencies import get_scene_master_repository
from recnavi.core.types.authenticated_user import AuthenticatedUser
from recnavi.core.types.x_user import XUser
from recnavi.main import app
from tests.mockups.mock_scene_master_repository import (
    MockSceneMasterRepository,
)
from tests.mockups.mock_users import get_mock_authenticated_user
from tests.mockups.mock_users import get_mock_x_user


@pytest.fixture(scope="session", autouse=True)
def client():
    """FastAPI test client with mocked authentication."""
    app.dependency_overrides[verify_user] = get_mock_x_user
    app.dependency_overrides[get_authenticated_user] = (
        get_mock_authenticated_user
    )
    app.dependency_overrides[get_scene_master_repository] = (
        MockSceneMasterRepository
    )

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
def mock_x_user() -> XUser:
    """Mock XUser for integration tests."""
    return get_mock_x_user()


@pytest.fixture
def mock_authenticated_user() -> AuthenticatedUser:
    """Mock AuthenticatedUser for integration tests."""
    return get_mock_authenticated_user()
