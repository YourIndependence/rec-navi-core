# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Tests for User type."""

import pytest

from recnavi.core.types.user import User
from recnavi.core.types.user import UserRole


@pytest.mark.parametrize(
    ("user_role", "requested_role", "expected"),
    [
        (UserRole.STAFF, UserRole.STAFF, True),
        (UserRole.STAFF, UserRole.OWNER, False),
        (UserRole.STAFF, UserRole.ADMIN, False),
        (UserRole.OWNER, UserRole.STAFF, True),
        (UserRole.OWNER, UserRole.OWNER, True),
        (UserRole.OWNER, UserRole.ADMIN, False),
        (UserRole.ADMIN, UserRole.STAFF, True),
        (UserRole.ADMIN, UserRole.OWNER, True),
        (UserRole.ADMIN, UserRole.ADMIN, True),
    ],
)
def test_can_act_as_respects_role_hierarchy(
    user_role,
    requested_role,
    expected,
):
    """Test users can act at their role or a lower role."""
    user = User(
        user_id="user-123",
        user_name="Test User",
        role=user_role,
        group_id="group-456",
    )

    assert user.can_act_as(requested_role) is expected
