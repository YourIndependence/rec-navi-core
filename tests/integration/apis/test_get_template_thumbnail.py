# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Integration tests for the getTemplateThumbnail endpoint."""

import pytest


def test_serves_the_tile_image(client):
    """The template tile comes back as raw bytes."""
    response = client.get(
        "/getTemplateThumbnail",
        params={"templateId": "tpl_cafe"},
    )

    assert response.status_code == 200
    assert response.content == b"tile-tpl_cafe"
    assert response.headers["content-type"] == "image/jpeg"


def test_asks_the_browser_to_keep_the_image(client):
    """The picker shows every tile at once, so caching matters."""
    response = client.get(
        "/getTemplateThumbnail",
        params={"templateId": "tpl_cafe"},
    )

    assert response.headers["cache-control"] == "public, max-age=86400"


def test_needs_no_token():
    """An img tag cannot send an Authorization header."""
    from recnavi.apis.master import master_router as module

    route = next(
        r
        for r in module.master_router.routes
        if r.path == "/getTemplateThumbnail"
    )

    assert route.dependencies == []


@pytest.mark.parametrize(
    ("params", "expected"),
    [
        ({"templateId": "tpl_nowhere"}, 404),
        ({}, 422),
    ],
)
def test_refuses_what_it_cannot_serve(client, params, expected):
    """An unknown template is missing; no identifier is a bad request."""
    response = client.get("/getTemplateThumbnail", params=params)

    assert response.status_code == expected
