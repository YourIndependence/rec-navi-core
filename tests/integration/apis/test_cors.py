# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""CORS preflight tests against the real app middleware."""

from fastapi.testclient import TestClient

from recnavi.main import app


ALLOWED_ORIGIN = "http://localhost:5173"
DENIED_ORIGIN = "http://evil.example.test"


def _preflight(*, origin: str) -> dict[str, str]:
    client = TestClient(app)
    response = client.options(
        "/health",
        headers={
            "Origin": origin,
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "Authorization",
        },
    )
    return dict(response.headers)


def test_preflight_from_allowed_origin_is_echoed() -> None:
    headers = _preflight(origin=ALLOWED_ORIGIN)
    assert headers.get("access-control-allow-origin") == ALLOWED_ORIGIN
    assert (
        "authorization"
        in headers.get(
            "access-control-allow-headers",
            "",
        ).lower()
    )


def test_preflight_from_disallowed_origin_is_not_allowed() -> None:
    headers = _preflight(origin=DENIED_ORIGIN)
    assert "access-control-allow-origin" not in headers
