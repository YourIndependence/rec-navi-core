# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or reproduction of this software is strictly prohibited.
#
# For internal use only.
# developer team.

"""Integration tests for the greeting endpoint."""

from recnavi.config.variables import ENV


def test_greeting_returns_success(client):
    """Return a successful greeting response."""
    response = client.get("/greeting")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert isinstance(data["timestamp"], int)
    assert data["environment"] == ENV
