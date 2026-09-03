# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Integration tests for the getSceneThumbnail endpoint."""

import pytest


def test_serves_the_example_photo(client):
    """The example kind returns the photo to imitate."""
    response = client.get(
        "/getSceneThumbnail",
        params={"scenePrincipal": "shop_gaikan", "kind": "example"},
    )

    assert response.status_code == 200
    assert response.content == b"example-shop_gaikan"
    assert response.headers["content-type"] == "image/jpeg"


def test_serves_the_framing_guide(client):
    """The guide kind returns the overlay."""
    response = client.get(
        "/getSceneThumbnail",
        params={"scenePrincipal": "shop_gaikan", "kind": "guide"},
    )

    assert response.status_code == 200
    assert response.content == b"guide-shop_gaikan"
    assert response.headers["content-type"] == "image/png"


def test_asks_the_browser_to_keep_the_image(client):
    """Without this header every app launch pulls dozens of images."""
    response = client.get(
        "/getSceneThumbnail",
        params={"scenePrincipal": "shop_gaikan", "kind": "example"},
    )

    assert response.headers["cache-control"] == "public, max-age=86400"


def test_needs_no_token():
    """An img tag cannot send an Authorization header."""
    from recnavi.apis.master import master_router as module

    route = next(
        r
        for r in module.master_router.routes
        if r.path == "/getSceneThumbnail"
    )

    assert route.dependencies == []


@pytest.mark.parametrize(
    ("params", "expected"),
    [
        ({"scenePrincipal": "nowhere", "kind": "example"}, 404),
        ({"scenePrincipal": "shop_gaikan", "kind": "sideways"}, 422),
        ({"kind": "example"}, 422),
    ],
)
def test_refuses_what_it_cannot_serve(client, params, expected):
    """An unknown scene is missing; an unknown kind is a bad request."""
    response = client.get("/getSceneThumbnail", params=params)

    assert response.status_code == expected
