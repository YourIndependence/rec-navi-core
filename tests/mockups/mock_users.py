# Copyright (c) 2026 YourIndependence. All rights reserved.

"""Deterministic users for API unit tests."""

from recnavi.core.types.user import User
from recnavi.core.types.user import UserRole


def get_mock_x_user() -> User:
    """Return an authenticated user without contacting an identity provider."""
    return User(
        user_id="test-user-123",
        user_name="Test User",
        role=UserRole.ADMIN,
        group_id="it-group",
    )
