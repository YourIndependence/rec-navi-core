# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Tests for scene URL attachment."""

from unittest.mock import AsyncMock

import pytest

from recnavi.core.project.scene_urls import SCENE_URL_EXPIRATION_SECONDS
from recnavi.core.project.scene_urls import attach_scene_urls
from recnavi.core.types.project import Project
from tests.mockups.mock_object_storage import MockObjectStorage


@pytest.mark.asyncio
async def test_empty_project_needs_no_presigned_urls():
    """Preserve an empty project without calling object storage."""
    project = build_project(scenes=[])
    storage = MockObjectStorage(bucket_name="bucket")
    storage.generate_presigned_url = AsyncMock()
    view = await attach_scene_urls(storage=storage, project=project)
    assert view.model_dump() == project.model_dump()
    storage.generate_presigned_url.assert_not_awaited()


@pytest.mark.asyncio
async def test_mixed_scenes_preserve_order_metadata_and_original_keys():
    """Handle absent, partial, and complete recording keys independently."""
    scenes = [
        {"sceneId": "empty", "scenePrincipal": "opening"},
        {
            "sceneId": "video",
            "scenePrincipal": "cooking",
            "videoKey": "video.mp4",
        },
        {
            "sceneId": "thumbnail",
            "scenePrincipal": "closing",
            "thumbnailKey": "thumbnail.jpg",
        },
        {
            "sceneId": "both",
            "scenePrincipal": "closing",
            "videoKey": "both.mp4",
            "thumbnailKey": "both.jpg",
        },
    ]
    project = build_project(scenes=scenes)
    original = project.model_dump()
    storage = MockObjectStorage(bucket_name="bucket")
    presign = AsyncMock(wraps=storage.generate_presigned_url)
    storage.generate_presigned_url = presign
    view = await attach_scene_urls(storage=storage, project=project)
    assert project.model_dump() == original
    assert [scene.scene_id for scene in view.scenes] == [
        scene.scene_id for scene in project.scenes
    ]
    for source, public in zip(project.scenes, view.scenes, strict=True):
        expected = source.model_dump(exclude={"video_key", "thumbnail_key"})
        for key, field in (
            (source.video_key, "video_url"),
            (source.thumbnail_key, "thumbnail_url"),
        ):
            expected[field] = (
                None
                if key is None
                else f"mock://bucket/{key}?expires={SCENE_URL_EXPIRATION_SECONDS}"
            )
        assert public.model_dump() == expected
    assert presign.await_count == 4


def build_project(*, scenes: list[dict[str, object]]) -> Project:
    return Project.model_validate(
        {
            "projectId": "proj-123",
            "groupId": "group-456",
            "projectName": "Test Project",
            "ownerUserId": "user-789",
            "createdAt": "2026-01-01T00:00:00Z",
            "scenes": scenes,
        },
    )


@pytest.mark.asyncio
async def test_attach_scene_urls_returns_null_urls_for_unrecorded_scene():
    """Unrecorded scenes get null videoUrl and thumbnailUrl."""
    project = build_project(
        scenes=[{"sceneId": "s1", "scenePrincipal": "opening"}],
    )

    view = await attach_scene_urls(
        storage=MockObjectStorage(bucket_name="bucket"),
        project=project,
    )

    assert view.scenes[0].video_url is None
    assert view.scenes[0].thumbnail_url is None


@pytest.mark.asyncio
async def test_attach_scene_urls_returns_urls_for_recorded_scene():
    """Recorded scenes get presigned URLs built from their keys."""
    project = build_project(
        scenes=[
            {
                "sceneId": "s1",
                "scenePrincipal": "opening",
                "status": "pending",
                "videoKey": "videos/s1.mp4",
                "thumbnailKey": "thumbnails/s1.jpg",
            },
        ],
    )
    expires = SCENE_URL_EXPIRATION_SECONDS

    view = await attach_scene_urls(
        storage=MockObjectStorage(bucket_name="bucket"),
        project=project,
    )

    scene = view.scenes[0]
    assert scene.video_url == f"mock://bucket/videos/s1.mp4?expires={expires}"
    assert scene.thumbnail_url == (
        f"mock://bucket/thumbnails/s1.jpg?expires={expires}"
    )
    assert scene.status == project.scenes[0].status


@pytest.mark.asyncio
async def test_attach_scene_urls_never_serializes_storage_keys():
    """Serialized view exposes camelCase URLs and no S3 keys."""
    project = build_project(
        scenes=[
            {
                "sceneId": "s1",
                "scenePrincipal": "opening",
                "videoKey": "videos/s1.mp4",
                "thumbnailKey": "thumbnails/s1.jpg",
            },
        ],
    )

    view = await attach_scene_urls(
        storage=MockObjectStorage(bucket_name="bucket"),
        project=project,
    )

    scene = view.model_dump(by_alias=True)["scenes"][0]
    assert "videoUrl" in scene
    assert "thumbnailUrl" in scene
    assert "videoKey" not in scene
    assert "thumbnailKey" not in scene
    assert view.project_id == "proj-123"
    assert view.group_id == "group-456"
