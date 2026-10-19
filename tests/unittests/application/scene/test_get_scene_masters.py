# Copyright (c) 2026 YourIndependence. All rights reserved.

"""Scene master listing orchestration."""

from unittest.mock import AsyncMock
from unittest.mock import patch

import pytest

from recnavi.application.scene.get_scene_masters import (
    get_scene_masters_usecase,
)
from recnavi.core.types.scene_master import SceneMaster
from tests.mockups.mock_database import MockDatabase
from tests.mockups.mock_object_storage import MockObjectStorage


@pytest.mark.asyncio
async def test_get_scene_masters_attaches_urls_and_returns_core_views():
    database = MockDatabase()
    storage = MockObjectStorage(bucket_name="media")
    scenes = [
        SceneMaster(
            scene_principal="cooking",
            title="Cooking",
            max_duration_seconds=60,
        ),
    ]
    expected_output = [
        SceneMaster(
            scene_principal="cooking",
            title="Cooking",
            max_duration_seconds=60,
            thumbnail_url="https://signed/image",
        ),
    ]
    with (
        patch(
            "recnavi.application.scene.get_scene_masters.get_scene_masters",
            new=AsyncMock(return_value=scenes),
        ) as get_masters,
        patch(
            "recnavi.application.scene.get_scene_masters.attach_scene_master_urls",
            new=AsyncMock(return_value=expected_output),
        ) as attach_urls,
    ):
        result = await get_scene_masters_usecase(
            scenes_db=database,
            storage=storage,
        )
    get_masters.assert_awaited_once_with(scenes_db=database)
    attach_urls.assert_awaited_once_with(scenes=scenes, storage=storage)
    assert result is expected_output
