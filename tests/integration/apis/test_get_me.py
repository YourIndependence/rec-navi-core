# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Integration tests for the getMe endpoint."""


def test_get_me(client, auth_headers):
    """Return the signed-in user and the tenant they belong to."""
    response = client.get("/getMe", headers=auth_headers)

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "message": None,
        "user": {
            "userId": "7f1c0f2e-0a3d-4a1b-9c2e-2b7a6d5e4f30",
            "userName": "Koki Ueno",
            "role": "owner",
        },
        "groupId": "grp_sushi_taro",
    }


def test_names_the_tenant_once(client, auth_headers):
    """The group is not repeated inside the member."""
    response = client.get("/getMe", headers=auth_headers)

    assert "groupId" not in response.json()["user"]
