# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or reproduction of this software is strictly prohibited.
#
# For internal use only.
# developer team.

"""Tests for update_scene_usecase."""

from unittest.mock import AsyncMock
from unittest.mock import patch

import pytest

from recnavi.application.scene.update_scene_usecase import update_scene_usecase
from tests.mockups.mock_object_storage import MockObjectStorage


@pytest.mark.asyncio
async def test_usecase_delegates_to_update_scene():
    """Test usecase delegates to core update_scene and returns its output."""
    mock_db = AsyncMock()
    storage = MockObjectStorage()
    expected_output = AsyncMock()

    with patch(
        "recnavi.application.scene.update_scene_usecase.update_scene",
        new=AsyncMock(return_value=expected_output),
    ) as mock_update:
        result = await update_scene_usecase(
            scenes_db=mock_db,
            scene_principal="test_scene",
            title="Test Scene",
            max_duration_seconds=5,
            example_image="base64_example_data",
            guide_image="base64_guide_data",
            bucket_name="test-bucket",
            storage=storage,
        )

    mock_update.assert_awaited_once_with(
        scenes_db=mock_db,
        scene_principal="test_scene",
        title="Test Scene",
        max_duration_seconds=5,
        example_image="base64_example_data",
        guide_image="base64_guide_data",
        bucket_name="test-bucket",
        storage=storage,
    )
    assert result is expected_output
