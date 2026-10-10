# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or reproduction of this software is strictly prohibited.
#
# For internal use only.
# developer team.

"""Integration tests for POST /updateTemplate endpoint."""

from recnavi.apis.auth.auth import verify_admin
from recnavi.core.types.user import User
from recnavi.core.types.user import UserRole
from recnavi.main import app


def _mock_verify_admin() -> User:
    return User(
        user_id="admin",
        user_name="admin",
        role=UserRole.ADMIN,
        group_id="group",
    )


def test_update_template_returns_400_when_no_token(client):
    """Test POST /updateTemplate returns 400 when no authorization header."""
    response = client.post(
        "/updateTemplate",
        json={
            "template": {
                "templateId": None,
                "title": "Cafe Template",
                "scenePrincipals": ["cooking", "interview"],
            },
            "thumbnailImage": "ZmFrZSB0aHVtYm5haWw=",
        },
    )
    assert response.status_code == 400
    data = response.json()
    assert data["status"] == "error"


def test_update_template_returns_422_when_template_is_missing(client):
    """Test POST /updateTemplate rejects the old flat payload shape."""
    app.dependency_overrides[verify_admin] = _mock_verify_admin
    try:
        response = client.post(
            "/updateTemplate",
            json={
                "templateId": "tpl-cafe",
                "title": "Cafe Template",
                "scenePrincipals": ["cooking"],
                "thumbnail": "ZmFrZSB0aHVtYm5haWw=",
            },
        )
    finally:
        app.dependency_overrides.pop(verify_admin, None)
    assert response.status_code == 422
