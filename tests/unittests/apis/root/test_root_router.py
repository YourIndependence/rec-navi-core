# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""HTTP boundary tests for root endpoints."""

from fastapi.testclient import TestClient

from recnavi.config.variables import ENV
from tests.mockups.mock_users import get_mock_x_user


def test_health_returns_ok(root_client: TestClient) -> None:
    response = root_client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_greeting_returns_environment_and_timestamp(
    root_client: TestClient,
) -> None:
    response = root_client.get("/greeting")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["environment"] == ENV
    assert isinstance(data["timestamp"], int)


def test_get_me_returns_authenticated_user(
    root_client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    response = root_client.get("/getMe", headers=auth_headers)

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "message": None,
        "groupId": get_mock_x_user().group_id,
        "user": get_mock_x_user().model_dump(by_alias=True, mode="json"),
    }
