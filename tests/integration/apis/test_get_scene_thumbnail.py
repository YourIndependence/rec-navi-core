# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or reproduction of this software is strictly prohibited.
#
# For internal use only.
# developer team.

"""Integration tests for GET /getSceneThumbnail endpoint."""


def test_get_scene_thumbnail_returns_400_when_kind_is_invalid(client):
    """Test GET /getSceneThumbnail returns 400 for an invalid kind (no auth required)."""
    response = client.get(
        "/getSceneThumbnail?scene_principal=cooking&kind=invalid",
    )
    assert response.status_code == 400
    data = response.json()
    assert data["status"] == "error"


def test_get_scene_thumbnail_returns_422_when_params_missing(client):
    """Test GET /getSceneThumbnail returns 422 when required query params are missing."""
    response = client.get("/getSceneThumbnail")
    assert response.status_code == 422
