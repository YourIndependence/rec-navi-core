# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or reproduction of this software is strictly prohibited.
#
# For internal use only.
# developer team.

"""Integration tests for POST /updateSceneMaster endpoint."""


def test_update_scene_master_returns_400_when_no_token(client):
    """Test POST /updateSceneMaster returns 400 when no authorization header."""
    response = client.post(
        "/updateSceneMaster",
        json={
            "scene": {
                "scenePrincipal": None,
                "title": "Cooking Scene",
                "maxDurationSeconds": 5,
            },
            "exampleImage": "ZmFrZSBpbWFnZQ==",
            "guideImage": "ZmFrZSBndWlkZQ==",
        },
    )
    assert response.status_code == 400
    data = response.json()
    assert data["status"] == "error"


def test_update_scene_master_returns_422_when_scene_is_missing(
    client, auth_headers
):
    """Test POST /updateSceneMaster rejects the old flat payload shape."""
    response = client.post(
        "/updateSceneMaster",
        headers=auth_headers,
        json={
            "scenePrincipal": "cooking",
            "title": "Cooking Scene",
            "maxDurationSeconds": 5,
        },
    )
    assert response.status_code == 422
