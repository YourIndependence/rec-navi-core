# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or reproduction of this software is strictly prohibited.
#
# For internal use only.
# developer team.

"""Integration tests for POST /updateScene endpoint."""


def test_update_scene_returns_400_when_no_token(client):
    """Test POST /updateScene returns 400 when no authorization header."""
    response = client.post(
        "/updateScene",
        json={
            "scenePrincipal": "cooking",
            "title": "Cooking Scene",
            "maxDurationSeconds": 60,
            "exampleImage": "ZmFrZSBpbWFnZQ==",
            "guideImage": "ZmFrZSBndWlkZQ==",
        },
    )
    assert response.status_code == 400
    data = response.json()
    assert data["status"] == "error"
