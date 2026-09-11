# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Tests for get_me_use_case."""

from unittest.mock import AsyncMock
from unittest.mock import patch

import pytest

from recnavi.application.user.get_me import get_me_use_case
from recnavi.core.types.user import User


@pytest.mark.asyncio
@patch("recnavi.application.user.get_me.get_user_by_id")
async def test_get_me_use_case_calls_core_with_correct_args(
    mock_get_user_by_id: AsyncMock,
):
    """Test that get_me_use_case calls get_user_by_id with correct arguments."""
    # Setup mock
    mock_user = User(
        user_id="user-123",
        user_name="Test User",
        role="admin",
        group_id="group-456",
    )
    mock_get_user_by_id.return_value = mock_user

    # Create mock database
    mock_db = AsyncMock()

    # Call use case
    result = await get_me_use_case(sub="user-123", user_db=mock_db)

    # Verify core function was called with correct arguments
    mock_get_user_by_id.assert_called_once_with(
        user_id="user-123",
        user_db=mock_db,
    )

    # Verify result is returned from core
    assert result == mock_user
