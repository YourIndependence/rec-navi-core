# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Integration tests for the request body size guard."""

from recnavi.main import MAX_REQUEST_BODY_BYTES


def test_request_body_over_limit_returns_413(client):
    """Test a body larger than the limit is rejected with 413."""
    response = client.post(
        "/getProject",
        content=b"x" * (MAX_REQUEST_BODY_BYTES + 1),
    )

    assert response.status_code == 413
    assert response.json() == {
        "status": "error",
        "message": "Request body is too large",
    }


def test_request_body_within_limit_is_not_rejected(client):
    """Test a normal body is not rejected by the size guard."""
    response = client.post("/getProject", json={"projectId": "proj-123"})

    assert response.status_code != 413


def test_chunked_request_body_over_limit_returns_413(client):
    response = client.post(
        "/getProject",
        content=iter([b"x" * MAX_REQUEST_BODY_BYTES, b"x"]),
    )
    assert "content-length" not in response.request.headers
    assert response.status_code == 413
    assert response.json()["message"] == "Request body is too large"


def test_request_body_at_exact_limit_reaches_authentication(client):
    response = client.post(
        "/getProject",
        content=b"x" * MAX_REQUEST_BODY_BYTES,
    )
    assert response.status_code == 401
    assert response.json()["message"] == "Authorization header is required."
