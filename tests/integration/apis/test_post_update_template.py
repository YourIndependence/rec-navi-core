# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or reproduction of this software is strictly prohibited.
#
# For internal use only.
# developer team.

"""Integration tests for POST /updateTemplate endpoint."""


def test_update_template_returns_400_when_no_token(client):
    """Test POST /updateTemplate returns 400 when no authorization header."""
    response = client.post(
        "/updateTemplate",
        json={
            "templateId": "tpl-cafe",
            "title": "Cafe Template",
            "scenePrincipals": ["cooking", "interview"],
            "thumbnail": "ZmFrZSB0aHVtYm5haWw=",
        },
    )
    assert response.status_code == 400
    data = response.json()
    assert data["status"] == "error"
