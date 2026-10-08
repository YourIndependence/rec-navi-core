# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Tests for create_user_usecase."""

from unittest.mock import AsyncMock
from unittest.mock import patch

import pytest

from recnavi.application.user.create_user import create_user_usecase
from recnavi.core.types.user import User
from recnavi.core.types.user import UserRole


@pytest.mark.asyncio
async def test_create_user_usecase_delegates_to_create_user():
    """Test usecase delegates to core create_user collaborator."""
    users_db = AsyncMock()
    provider = AsyncMock()
    caller = User(
        user_id="owner-1",
        user_name="Owner",
        role=UserRole.OWNER,
        group_id="group-1",
    )
    expected_output = [object()]

    with patch(
        "recnavi.application.user.create_user.create_user",
        new=AsyncMock(return_value=expected_output),
    ) as mock_create:
        result = await create_user_usecase(
            users_db=users_db,
            identity_provider=provider,
            caller=caller,
            email="staff@example.com",
            user_name="Staff",
            role=UserRole.STAFF,
        )

    mock_create.assert_awaited_once_with(
        users_db=users_db,
        identity_provider=provider,
        caller=caller,
        email="staff@example.com",
        user_name="Staff",
        role=UserRole.STAFF,
    )
    assert result is expected_output
