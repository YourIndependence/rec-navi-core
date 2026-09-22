# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or reproduction of this software is strictly prohibited.
#
# For internal use only.
# developer team.

"""Unit tests for SceneInput type."""

from recnavi.core.types.scene_input import SceneInput


def test_scene_input_with_null_scene_id():
    """Test SceneInput can have None scene_id for new scenes."""
    scene_input = SceneInput(
        scene_id=None,
        scene_principal="cooking",
        assigned_user_ids=["user-1", "user-2"],
    )

    assert scene_input.scene_id is None
    assert scene_input.scene_principal == "cooking"
    assert scene_input.assigned_user_ids == ["user-1", "user-2"]


def test_scene_input_with_scene_id():
    """Test SceneInput can have scene_id for existing scenes."""
    scene_input = SceneInput(
        scene_id="scene-123",
        scene_principal="eating",
        assigned_user_ids=[],
    )

    assert scene_input.scene_id == "scene-123"
    assert scene_input.scene_principal == "eating"
    assert scene_input.assigned_user_ids == []


def test_scene_input_does_not_have_read_only_fields():
    """Test SceneInput excludes read-only fields (status, video_key, etc)."""
    scene_input = SceneInput(
        scene_id="scene-123",
        scene_principal="cooking",
        assigned_user_ids=[],
    )

    assert not hasattr(scene_input, "status")
    assert not hasattr(scene_input, "video_key")
    assert not hasattr(scene_input, "thumbnail_key")
    assert not hasattr(scene_input, "created_by")
    assert not hasattr(scene_input, "created_at")
