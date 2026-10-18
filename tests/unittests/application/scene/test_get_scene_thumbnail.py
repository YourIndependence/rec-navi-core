# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Tests for get_scene_thumbnail_usecase."""

from unittest.mock import AsyncMock
from unittest.mock import patch

import pytest

from recnavi.application.scene.get_scene_thumbnail import (
    get_scene_thumbnail_usecase,
)
from tests.mockups.mock_object_storage import MockObjectStorage


@pytest.mark.asyncio
async def test_usecase_delegates_to_get_scene_thumbnail():
    """Test usecase delegates to core get_scene_thumbnail collaborator."""
    mock_db = AsyncMock()
    mock_storage = MockObjectStorage(bucket_name="test-bucket")
    expected_stream = b"image"
    expected_content_type = "image/jpeg"
    expected_output = (expected_stream, expected_content_type)

    with patch(
        "recnavi.application.scene.get_scene_thumbnail.get_scene_thumbnail",
        new=AsyncMock(return_value=expected_output),
    ) as mock_get:
        result = await get_scene_thumbnail_usecase(
            scenes_db=mock_db,
            scene_principal="cooking",
            kind="example",
            storage=mock_storage,
        )

    mock_get.assert_awaited_once_with(
        scenes_db=mock_db,
        scene_principal="cooking",
        kind="example",
        storage=mock_storage,
    )
    assert result is expected_output
