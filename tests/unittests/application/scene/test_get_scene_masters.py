# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Tests for get_scene_masters use case."""

from unittest.mock import AsyncMock
from unittest.mock import patch

import pytest

from recnavi.application.scene.get_scene_masters import (
    get_scene_masters_usecase,
)
from tests.mockups.mock_database import MockDatabase


@pytest.mark.asyncio
async def test_get_scene_masters_usecase_delegates_to_core():
    """Test get_scene_masters_usecase delegates and returns the core output."""
    scenes_db = MockDatabase()
    expected_output = object()

    with patch(
        "recnavi.application.scene.get_scene_masters.get_scene_masters",
        new=AsyncMock(return_value=expected_output),
    ) as mock_get_scene_masters:
        result = await get_scene_masters_usecase(scenes_db=scenes_db)

    mock_get_scene_masters.assert_awaited_with(scenes_db=scenes_db)
    assert result is expected_output
