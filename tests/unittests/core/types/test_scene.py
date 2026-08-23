# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.


"""Scene tests"""

import pytest
from pydantic import ValidationError

from recnavi.core.types.scene import Scene
from recnavi.core.types.scene import SceneStatus


RECORDED = {
    "sceneId": "sc_a1",
    "scenePrincipal": "shop_gaikan",
    "status": "approve",
    "videoKey": "projects/proj_001/scenes/sc_a1/shot_7f3.mp4",
    "thumbnailKey": "projects/proj_001/scenes/sc_a1/shot_7f3_thumb.jpg",
    "createdBy": "user_suzuki",
    "createdAt": "2026-08-14T10:12:00Z",
    "assignedAt": "2026-08-14T09:00:00Z",
    "assignedUserIds": ["user_suzuki"],
}


def test_statuses():
    assert [status.value for status in SceneStatus] == [
        "not_recorded",
        "pending",
        "reject",
        "approve",
    ]


def test_load_recorded_scene():
    scene = Scene.model_validate(RECORDED)

    assert scene.scene_id == "sc_a1"
    assert scene.status is SceneStatus.APPROVE
    assert scene.created_by == "user_suzuki"


def test_dump_keeps_camel_case():
    scene = Scene.model_validate(RECORDED)

    assert scene.model_dump(by_alias=True, mode="json") == RECORDED


def test_defaults_before_recording():
    scene = Scene.model_validate(
        {"sceneId": "sc_d4", "scenePrincipal": "main_dish"},
    )

    assert scene.status is SceneStatus.NOT_RECORDED
    assert scene.video_key is None
    assert scene.thumbnail_key is None
    assert scene.created_by is None
    assert scene.created_at is None
    assert scene.assigned_user_ids == []


def test_reject_unknown_status():
    with pytest.raises(ValidationError):
        Scene.model_validate(
            {
                "sceneId": "sc_x",
                "scenePrincipal": "main_dish",
                "status": "bogus",
            },
        )
