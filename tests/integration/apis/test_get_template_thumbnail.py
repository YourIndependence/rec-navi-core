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
    """Test GET /getTemplateThumbnail returns 422 when missing template_id."""
    response = client.get("/getTemplateThumbnail")
    assert response.status_code == 422
