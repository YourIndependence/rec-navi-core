# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or reproduction of this software is strictly prohibited.
#
# For internal use only.
# developer team.

"""Tests for auth module."""

from unittest.mock import AsyncMock

import pytest

from recnavi.apis.auth.auth import verify_admin
from recnavi.core.types.user import User
from recnavi.core.types.user import UserRole
from recnavi.exceptions.exceptions import ClientAuthorizationError


@pytest.mark.asyncio
async def test_verify_admin_allows_admin_user():
    """Test verify_admin allows admin users."""
    admin_user = User(
        user_id="admin-1",
        user_name="Admin User",
        role=UserRole.ADMIN,
        group_id="group-1",
    )

    mock_request = AsyncMock()
    mock_request.app.state.database = {}

    # Mock verify_user to return admin
    from unittest.mock import patch

    with patch(
        "recnavi.apis.auth.auth.verify_user",
        return_value=admin_user,
    ):
        result = await verify_admin(mock_request)

    assert result == admin_user


@pytest.mark.asyncio
async def test_verify_admin_raises_403_for_owner():
    """Test verify_admin raises 403 for owner users."""
    owner_user = User(
        user_id="owner-1",
        user_name="Owner User",
        role=UserRole.OWNER,
        group_id="group-1",
    )

    mock_request = AsyncMock()

    from unittest.mock import patch

    with patch(
        "recnavi.apis.auth.auth.verify_user",
        return_value=owner_user,
    ):
        with pytest.raises(ClientAuthorizationError, match="forbidden"):
            await verify_admin(mock_request)


@pytest.mark.asyncio
async def test_verify_admin_raises_403_for_staff():
    """Test verify_admin raises 403 for staff users."""
    staff_user = User(
        user_id="staff-1",
        user_name="Staff User",
        role=UserRole.STAFF,
        group_id="group-1",
    )

    mock_request = AsyncMock()

    from unittest.mock import patch

    with patch(
        "recnavi.apis.auth.auth.verify_user",
        return_value=staff_user,
    ):
        with pytest.raises(ClientAuthorizationError, match="forbidden"):
            await verify_admin(mock_request)
