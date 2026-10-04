# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Tests for Scene type."""

from recnavi.core.types.scene import Scene
from recnavi.core.types.scene import SceneStatus


def test_scene_has_optional_review_fields():
    """Test Scene type has optional review metadata fields."""
    scene = Scene(
        scene_id="scene-123",
        scene_principal="cooking",
        status=SceneStatus.APPROVE,
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
