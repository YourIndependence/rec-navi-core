# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Integration tests for the getSceneMasters endpoint."""


def test_get_scene_masters(client, auth_headers):
    """Return every scene master through the app."""
    response = client.get("/getSceneMasters", headers=auth_headers)

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "message": None,
        "scenes": [
            {
                "scenePrincipal": "shop_gaikan",
                "title": "Shop exterior",
                "maxDurationSeconds": 5,
            },
            {
                "scenePrincipal": "main_dish",
                "title": "Signature dish",
                "maxDurationSeconds": 3,
            },
        ],
    }


def test_no_object_key_reaches_the_client(client, auth_headers):
    """Where the images are stored stays on the server."""
    response = client.get("/getSceneMasters", headers=auth_headers)

    assert response.status_code == 200
    assert "thumbnailUri" not in response.text
    assert "guideUri" not in response.text
    assert "masters/" not in response.text
