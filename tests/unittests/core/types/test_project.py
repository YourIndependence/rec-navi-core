# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.


"""Project tests"""

import pytest
from pydantic import ValidationError

from recnavi.core.types.project import Project
from recnavi.core.types.project import ProjectStatus
from recnavi.core.types.scene import SceneStatus


PROJECT = {
    "projectId": "proj_001",
    "groupId": "group_acme",
    "projectName": "Shibuya store",
    "ownerUserId": "user_tanaka",
    "createdAt": "2026-08-14T09:00:00Z",
    "description": "2026-08-14 14:00",
    "scenes": [
        {
            "sceneId": "sc_a1",
            "scenePrincipal": "shop_gaikan",
            "status": "approve",
            "videoKey": "projects/proj_001/scenes/sc_a1/shot_7f3.mp4",
            "thumbnailKey": "projects/proj_001/scenes/sc_a1/thumb.jpg",
            "createdBy": "user_suzuki",
            "createdAt": "2026-08-14T10:12:00Z",
            "assignedAt": "2026-08-14T09:00:00Z",
            "assignedUserIds": ["user_suzuki"],
        },
    ],
    "assignedUserIds": ["user_suzuki", "user_sato"],
    "status": "in_progress",
}


def test_statuses():
    assert [status.value for status in ProjectStatus] == [
        "in_progress",
        "submitted",
    ]


def test_load_project_with_scenes():
    project = Project.model_validate(PROJECT)

    assert project.project_id == "proj_001"
    assert project.status is ProjectStatus.IN_PROGRESS
    assert project.scenes[0].scene_id == "sc_a1"
    assert project.scenes[0].status is SceneStatus.APPROVE


def test_dump_keeps_camel_case():
    project = Project.model_validate(PROJECT)

    assert project.model_dump(by_alias=True, mode="json") == PROJECT


def test_defaults_of_a_new_project():
    project = Project.model_validate(
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


def test_reject_missing_identifier():
    item = {key: value for key, value in PROJECT.items() if key != "projectId"}

    with pytest.raises(ValidationError):
        Project.model_validate(item)
