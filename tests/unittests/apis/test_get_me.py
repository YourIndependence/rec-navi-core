# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.


"""Tests for the getMe endpoint response."""

import pytest

from recnavi.apis.root.root_router import get_me
from recnavi.core.types.user import User
from recnavi.core.types.user import UserRole


@pytest.mark.asyncio
async def test_get_me_returns_user_and_group_id():
    """Test get_me returns the user and a top-level groupId."""
    user = User(
        user_id="user-1",
        user_name="User 1",
        group_id="group-1",
        role=UserRole.OWNER,
    )

    response = await get_me(user=user)

    dumped = response.model_dump(by_alias=True)
    assert dumped["groupId"] == "group-1"
    assert dumped["user"]["userId"] == "user-1"
    assert dumped["user"]["groupId"] == "group-1"
