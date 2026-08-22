# Copyright (c) 2025 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.


"""ProjectTableItem tests"""

import pytest
from pydantic import ValidationError

from recnavi.core.types.project_table_item import ProjectStatus
from recnavi.core.types.project_table_item import ProjectTableItem
from recnavi.core.types.project_table_item import Scene
from recnavi.core.types.project_table_item import SceneStatus


RECORDED_SCENE = {
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

ITEM = {
    "projectId": "proj_001",
    "groupId": "group_acme",
    "projectName": "Shibuya store",
    "ownerUserId": "user_tanaka",
    "createdAt": "2026-08-14T09:00:00Z",
    "description": "2026-08-14 14:00",
    "scenes": [RECORDED_SCENE],
    "assignedUserIds": ["user_suzuki", "user_sato"],
    "status": "in_progress",
}


def test_statuses():
    assert [status.value for status in SceneStatus] == [
        "not_recorded",
        "pending",
        "reject",
        "approve",
    ]
    assert [status.value for status in ProjectStatus] == [
        "in_progress",
        "submitted",
    ]


def test_load_from_table_item():
    project = ProjectTableItem.model_validate(ITEM)

    assert project.project_id == "proj_001"
    assert project.status is ProjectStatus.IN_PROGRESS
    assert project.scenes[0].scene_id == "sc_a1"
    assert project.scenes[0].status is SceneStatus.APPROVE


def test_dump_to_table_item():
    project = ProjectTableItem.model_validate(ITEM)

    assert project.model_dump(by_alias=True, mode="json") == ITEM


def test_scene_defaults_before_recording():
    scene = Scene.model_validate(
        {"sceneId": "sc_d4", "scenePrincipal": "main_dish"},
    )

    assert scene.status is SceneStatus.NOT_RECORDED
    assert scene.video_key is None
    assert scene.thumbnail_key is None
    assert scene.created_by is None
    assert scene.created_at is None
    assert scene.assigned_user_ids == []


def test_project_defaults():
    project = ProjectTableItem.model_validate(
        {
            "projectId": "proj_002",
            "groupId": "group_acme",
            "projectName": "Shinjuku store",
            "ownerUserId": "user_tanaka",
            "createdAt": "2026-08-15T09:00:00Z",
        },
    )

    assert project.status is ProjectStatus.IN_PROGRESS
    assert project.scenes == []
    assert project.assigned_user_ids == []
    assert project.description == ""


def test_reject_unknown_scene_status():
    with pytest.raises(ValidationError):
        Scene.model_validate(
            {
                "sceneId": "sc_x",
                "scenePrincipal": "main_dish",
                "status": "bogus",
            },
        )


def test_reject_missing_partition_key():
    item = {key: value for key, value in ITEM.items() if key != "projectId"}

    with pytest.raises(ValidationError):
        ProjectTableItem.model_validate(item)
