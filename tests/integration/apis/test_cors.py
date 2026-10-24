# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""CORS preflight tests against the real app middleware."""

ALLOWED_ORIGIN = "http://localhost:5173"
DENIED_ORIGIN = "http://evil.example.test"


def test_preflight_from_allowed_origin_is_echoed(client) -> None:
    response = client.options(
        "/health",
        headers={
            "Origin": ALLOWED_ORIGIN,
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "Authorization",
        },
    )
    assert response.status_code == 200
    assert (
        response.headers.get("access-control-allow-origin") == ALLOWED_ORIGIN
    )
    assert (
        "authorization"
        in response.headers.get("access-control-allow-headers", "").lower()
    )


def test_preflight_from_disallowed_origin_is_not_allowed(client) -> None:
    response = client.options(
        "/health",
        headers={
            "Origin": DENIED_ORIGIN,
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "Authorization",
        },
    )
    assert response.status_code == 400
    assert "access-control-allow-origin" not in response.headers
