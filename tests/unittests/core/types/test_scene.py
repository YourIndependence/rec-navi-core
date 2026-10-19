# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Tests for Scene type."""

from unittest.mock import AsyncMock

import pytest

from recnavi.core.types.scene import ReviewSceneResult
from recnavi.core.types.scene import Scene
from recnavi.core.types.scene import SceneStatus
from tests.mockups.mock_object_storage import MockObjectStorage


def test_scene_has_optional_review_fields():
    """Test Scene type has optional review metadata fields."""
    scene = Scene(
        scene_id="scene-123",
        scene_principal="cooking",
        status=SceneStatus.APPROVED,
        reviewed_by="owner-001",
        reviewed_at="2026-09-23T12:00:00Z",
        review_comment="Looks good!",
    )

    assert scene.reviewed_by == "owner-001"
    assert scene.reviewed_at == "2026-09-23T12:00:00Z"
    assert scene.review_comment == "Looks good!"


def test_scene_review_fields_default_to_none():
    """Test Scene review fields default to None."""
    scene = Scene(
        scene_id="scene-123",
        scene_principal="cooking",
    )

    assert scene.reviewed_by is None
    assert scene.reviewed_at is None
    assert scene.review_comment is None


def test_scene_preserves_existing_fields():
    """Test Scene type preserves all existing fields."""
    scene = Scene(
        scene_id="scene-123",
        scene_principal="cooking",
        status=SceneStatus.PENDING,
        video_key="projects/proj-1/scenes/scene-123/shot-456.mp4",
        thumbnail_key="projects/proj-1/scenes/scene-123/shot-456_thumb.jpg",
        created_by="staff-001",
        created_at="2026-09-20T10:00:00Z",
        assigned_user_ids=["staff-001", "staff-002"],
    )

    assert scene.scene_id == "scene-123"
    assert scene.scene_principal == "cooking"
    assert scene.status == SceneStatus.PENDING
    assert scene.video_key == "projects/proj-1/scenes/scene-123/shot-456.mp4"
    assert (
        scene.thumbnail_key
        == "projects/proj-1/scenes/scene-123/shot-456_thumb.jpg"
    )
    assert scene.created_by == "staff-001"
    assert scene.created_at == "2026-09-20T10:00:00Z"
    assert scene.assigned_user_ids == ["staff-001", "staff-002"]


def test_review_results_share_scene_status_values() -> None:
    """Review decisions are the approved/rejected subset of scene states."""
    assert {result.value for result in ReviewSceneResult} == {
        SceneStatus.APPROVED.value,
        SceneStatus.REJECTED.value,
    }
    for result in ReviewSceneResult:
        assert SceneStatus(result.value).name == result.name


@pytest.mark.asyncio
async def test_scene_urls_refresh_and_storage_round_trip_preserves_keys():
    scene = Scene(
        scene_id="scene",
        scene_principal="opening",
        video_key="video.mp4",
        thumbnail_key="thumb.jpg",
        assigned_user_ids=["staff"],
    )
    storage = MockObjectStorage(bucket_name="media")
    storage.generate_presigned_url = AsyncMock(
        side_effect=[
            "https://signed/video-1",
            "https://signed/thumb-1",
            "https://signed/video-2",
            "https://signed/thumb-2",
        ],
    )
    first = await scene.attach_presigned_url(storage=storage)
    second = await first.attach_presigned_url(storage=storage)
    second.assigned_user_ids.append("another")
    assert scene.assigned_user_ids == first.assigned_user_ids == ["staff"]
    assert scene.video_url is None
    assert first.video_url == "https://signed/video-1"
    assert second.video_url == "https://signed/video-2"
    restored = Scene.model_validate(first.to_storage_item())
    assert restored == scene
    assert first.to_storage_item()["videoKey"] == "video.mp4"
    assert "videoUrl" not in first.to_storage_item()
    assert "thumbnailUrl" not in first.to_storage_item()
    assert "videoKey" not in first.model_dump(by_alias=True)
    assert "thumbnailKey" not in first.model_dump(by_alias=True)


def test_scene_response_schema_excludes_storage_keys():
    properties = Scene.model_json_schema(mode="serialization")["properties"]
    assert "videoKey" not in properties
    assert "thumbnailKey" not in properties
    assert "videoUrl" in properties
    assert "thumbnailUrl" in properties
