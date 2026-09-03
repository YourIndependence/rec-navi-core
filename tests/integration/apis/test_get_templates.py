# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Integration tests for the getTemplates endpoint."""


def test_get_templates(client, auth_headers):
    """Return every scenes template through the app."""
    response = client.get("/getTemplates", headers=auth_headers)

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "message": None,
        "templates": [
            {
                "templateId": "tpl_cafe",
                "title": "Cafe",
                "scenePrincipals": [
                    "shop_gaikan",
                    "main_dish",
                    "main_dish",
                ],
            },
            {
                "templateId": "tpl_hotel",
                "title": "Hotel",
                "scenePrincipals": ["shop_gaikan", "room"],
            },
        ],
    }


def test_no_object_key_reaches_the_client(client, auth_headers):
    """Where the tile images are stored stays on the server."""
    response = client.get("/getTemplates", headers=auth_headers)

    assert response.status_code == 200
    assert "thumbnailUri" not in response.text
    assert "assets/" not in response.text
