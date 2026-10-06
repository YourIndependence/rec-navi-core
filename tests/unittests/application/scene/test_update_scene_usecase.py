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
from recnavi.exceptions.exceptions import ClientUnprocessableEntityError
from tests.mockups.mock_database import MockDatabase


@pytest.mark.asyncio
async def test_update_scene_usecase_delegates_to_upsert_scene_master():
    """Test usecase delegates to core upsert_scene_master collaborator."""
    scenes_db = MockDatabase()
    await scenes_db.put_item(
        {
            "scenePrincipal": "existing_scene",
            "title": "Old Title",
            "maxDurationSeconds": 3,
            "thumbnailUri": "s3://test-bucket/scenes/existing_scene/example.jpg",
            "guideUri": "s3://test-bucket/scenes/existing_scene/guide.jpg",
        },
    )

    with (
        patch(
            "recnavi.application.scene.update_scene_usecase.upload_base64",
            new=AsyncMock(),
        ),
        patch(
            "recnavi.application.scene.update_scene_usecase.upsert_scene_master",
            new=AsyncMock(),
        ) as mock_upsert,
        patch.object(
            scenes_db,
            "scan",
            new=AsyncMock(
                return_value=type(
                    "Result",
                    (),
                    {
                        "items": [
                            {
                                "scenePrincipal": "existing_scene",
                                "title": "Updated Title",
                                "maxDurationSeconds": 7,
                                "thumbnailUri": "s3://test-bucket/scenes/existing_scene/example.jpg",
                                "guideUri": "s3://test-bucket/scenes/existing_scene/guide.jpg",
                            },
                        ],
                    },
                )(),
            ),
        ),
    ):
        result = await update_scene_usecase(
            scenes_db=scenes_db,
            scene_principal="existing_scene",
            title="Updated Title",
            max_duration_seconds=7,
            example_image=None,
            guide_image=None,
            bucket_name="test-bucket",
        )

    mock_upsert.assert_awaited_once_with(
        scenes_db=scenes_db,
        scene_principal="existing_scene",
        title="Updated Title",
        max_duration_seconds=7,
        thumbnail_uri="s3://test-bucket/scenes/existing_scene/example.jpg",
        guide_uri="s3://test-bucket/scenes/existing_scene/guide.jpg",
    )
    assert len(result) == 1
    assert result[0].scene_principal == "existing_scene"


@pytest.mark.asyncio
async def test_update_scene_usecase_creates_scene_with_images():
    """Test usecase creates new scene with uploaded images."""
    scenes_db = MockDatabase()

    mock_upload_base64 = AsyncMock()

    with patch(
        "recnavi.application.scene.update_scene_usecase.upload_base64",
        mock_upload_base64,
    ):
        scenes = await update_scene_usecase(
            scenes_db=scenes_db,
            scene_principal="new_scene",
            title="New Scene",
            max_duration_seconds=5,
            example_image="base64_example_data",
            guide_image="base64_guide_data",
            bucket_name="test-bucket",
        )

    assert len(scenes) == 1
    assert scenes[0].scene_principal == "new_scene"
    assert scenes[0].title == "New Scene"
    assert scenes[0].max_duration_seconds == 5

    assert mock_upload_base64.call_count == 2
    mock_upload_base64.assert_any_call(
        bucket_name="test-bucket",
        object_key="scenes/new_scene/example.jpg",
        base64_data="base64_example_data",
        content_type="image/jpeg",
    )
    mock_upload_base64.assert_any_call(
        bucket_name="test-bucket",
        object_key="scenes/new_scene/guide.jpg",
        base64_data="base64_guide_data",
        content_type="image/jpeg",
    )


@pytest.mark.asyncio
async def test_update_scene_usecase_updates_scene_without_images():
    """Test usecase updates existing scene without changing images."""
    scenes_db = MockDatabase()
    await scenes_db.put_item(
        {
            "scenePrincipal": "existing_scene",
            "title": "Old Title",
            "maxDurationSeconds": 3,
            "thumbnailUri": "s3://test-bucket/scenes/existing_scene/example.jpg",
            "guideUri": "s3://test-bucket/scenes/existing_scene/guide.jpg",
        },
    )

    mock_upload_base64 = AsyncMock()

    with patch(
        "recnavi.application.scene.update_scene_usecase.upload_base64",
        mock_upload_base64,
    ):
        scenes = await update_scene_usecase(
            scenes_db=scenes_db,
            scene_principal="existing_scene",
            title="Updated Title",
            max_duration_seconds=7,
            example_image=None,
            guide_image=None,
            bucket_name="test-bucket",
        )

    assert len(scenes) == 1
    assert scenes[0].scene_principal == "existing_scene"
    assert scenes[0].title == "Updated Title"
    assert scenes[0].max_duration_seconds == 7
    assert (
        scenes[0].thumbnail_uri
        == "s3://test-bucket/scenes/existing_scene/example.jpg"
    )
    assert (
        scenes[0].guide_uri
        == "s3://test-bucket/scenes/existing_scene/guide.jpg"
    )

    mock_upload_base64.assert_not_called()


@pytest.mark.asyncio
async def test_update_scene_usecase_raises_422_when_images_missing_on_create():
    """Test usecase raises 422 when creating without images."""
    scenes_db = MockDatabase()

    with pytest.raises(
        ClientUnprocessableEntityError,
        match="exampleImage and guideImage are required when creating a new scene",
    ):
        await update_scene_usecase(
            scenes_db=scenes_db,
            scene_principal="new_scene",
            title="New Scene",
            max_duration_seconds=5,
            example_image=None,
            guide_image=None,
            bucket_name="test-bucket",
        )


@pytest.mark.asyncio
async def test_update_scene_usecase_updates_only_example_image():
    """Test usecase updates only example image when provided."""
    scenes_db = MockDatabase()
    await scenes_db.put_item(
        {
            "scenePrincipal": "existing_scene",
            "title": "Title",
            "maxDurationSeconds": 5,
            "thumbnailUri": "s3://test-bucket/scenes/existing_scene/example.jpg",
            "guideUri": "s3://test-bucket/scenes/existing_scene/guide.jpg",
        },
    )

    mock_upload_base64 = AsyncMock()

    with patch(
        "recnavi.application.scene.update_scene_usecase.upload_base64",
        mock_upload_base64,
    ):
        scenes = await update_scene_usecase(
            scenes_db=scenes_db,
            scene_principal="existing_scene",
            title="Title",
            max_duration_seconds=5,
            example_image="new_base64_example",
            guide_image=None,
            bucket_name="test-bucket",
        )

    assert len(scenes) == 1

    mock_upload_base64.assert_called_once_with(
        bucket_name="test-bucket",
        object_key="scenes/existing_scene/example.jpg",
        base64_data="new_base64_example",
        content_type="image/jpeg",
    )
