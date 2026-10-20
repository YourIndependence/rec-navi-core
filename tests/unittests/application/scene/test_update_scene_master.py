# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or reproduction of this software is strictly prohibited.
#
# For internal use only.
# developer team.

"""Tests for update_scene_master_usecase."""

from unittest.mock import AsyncMock
from unittest.mock import patch

import pytest

from recnavi.application.scene.update_scene_master import (
    update_scene_master_usecase,
)
from tests.mockups.mock_object_storage import MockObjectStorage
from tests.mockups.mock_users import get_mock_x_user


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("title", "duration"),
    [("Test Scene", 5), (None, 7), ("Renamed", None), (None, None)],
)
async def test_usecase_delegates_to_update_scene_master(title, duration):
    """Test usecase delegates to core update_scene_master and attaches image URLs."""
    mock_db = AsyncMock()
    storage = MockObjectStorage(bucket_name="test-bucket")
    expected_output = AsyncMock()
    expected_output.attach_presigned_url.return_value = expected_output

    with patch(
        "recnavi.application.scene.update_scene_master.update_scene_master",
        new=AsyncMock(return_value=expected_output),
    ) as mock_update:
        result = await update_scene_master_usecase(
            scenes_db=mock_db,
            user=get_mock_x_user(),
            scene_principal="test_scene",
            title=title,
            max_duration_seconds=duration,
            example_image="base64_example_data",
            guide_image="base64_guide_data",
            storage=storage,
        )

    mock_update.assert_awaited_once_with(
        scenes_db=mock_db,
        user=get_mock_x_user(),
        scene_principal="test_scene",
        title=title,
        max_duration_seconds=duration,
        example_image="base64_example_data",
        guide_image="base64_guide_data",
        storage=storage,
    )
    expected_output.attach_presigned_url.assert_awaited_once_with(
        storage=storage,
    )
    assert result is expected_output
