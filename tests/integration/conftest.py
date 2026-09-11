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

from recnavi.main import app


@pytest.fixture(scope="session", autouse=True)
def client():
    """FastAPI test client with mocked authentication."""

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
