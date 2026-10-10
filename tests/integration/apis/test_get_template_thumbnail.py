# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or reproduction of this software is strictly prohibited.
#
# For internal use only.
# developer team.

"""Integration tests for GET /getTemplateThumbnail endpoint."""


def test_get_template_thumbnail_returns_422_when_missing_param(client):
    """Test GET /getTemplateThumbnail returns 422 when missing templateId."""
    response = client.get("/getTemplateThumbnail")
    assert response.status_code == 422


def test_get_template_thumbnail_returns_422_for_snake_case_param(client):
    """Test GET /getTemplateThumbnail rejects the old snake_case template_id name."""
    response = client.get("/getTemplateThumbnail?template_id=unknown-template")
    assert response.status_code == 422


def test_get_template_thumbnail_accepts_camel_case_param(client):
    """Test GET /getTemplateThumbnail accepts templateId (designed URL) and is not 422."""
    response = client.get("/getTemplateThumbnail?templateId=unknown-template")
    assert response.status_code != 422
