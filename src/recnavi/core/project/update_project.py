# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Update project with optimistic locking."""

from datetime import UTC
from datetime import datetime

from recnavi.core.database.base_database import BaseDatabase
from recnavi.core.types.project import Project
from recnavi.core.types.scene import Scene
from recnavi.core.types.scene import SceneStatus
from recnavi.core.types.scene_input import SceneInput
from recnavi.core.types.user import User
from recnavi.core.types.user import UserRole
from recnavi.exceptions.exceptions import ClientAuthorizationError
from recnavi.exceptions.exceptions import ClientConflictError
from recnavi.exceptions.exceptions import ClientResourcesNotFoundError


def merge_scenes(
    *,
    existing_scenes: list[Scene],
    scene_inputs: list[SceneInput],
) -> list[Scene]:
    """Merge scene inputs with existing scenes."""
    existing_by_id = {scene.scene_id: scene for scene in existing_scenes}
    merged = []

    for scene_input in scene_inputs:
        existing_scene = existing_by_id.get(scene_input.scene_id)
        if existing_scene:
            merged.append(
                existing_scene.model_copy(
                    update={
                        "scene_principal": scene_input.scene_principal,
                        "assigned_user_ids": scene_input.assigned_user_ids,
                    },
                ),
            )
        else:
            merged.append(
                Scene(
                    scene_id=scene_input.scene_id,
                    scene_principal=scene_input.scene_principal,
                    assigned_user_ids=scene_input.assigned_user_ids,
                    status=SceneStatus.NOT_RECORDED,
                ),
            )

    return merged


async def validate_assignees_in_group(
    *,
    users_db: BaseDatabase,
    assigned_user_ids: list[str],
    scenes: list[SceneInput],
    group_id: str,
) -> None:
    """Ensure every assignee is a user of the given group."""
    user_ids = set(assigned_user_ids)
    for scene in scenes:
        user_ids.update(scene.assigned_user_ids)

    for user_id in user_ids:
        user_item = await users_db.get_item(key={"userId": user_id})
        if not user_item or user_item.get("groupId") != group_id:
            raise ClientAuthorizationError(
                "Assigned users must belong to your group",
            )


async def update_project(
    *,
    projects_db: BaseDatabase,
    users_db: BaseDatabase,
    project_id: str,
    project_name: str,
    description: str,
    assigned_user_ids: list[str],
    scenes: list[SceneInput],
    expected_version: int,
    user: User,
) -> Project:
    """Update project with optimistic locking."""
    existing_item = await projects_db.get_item({"projectId": project_id})
    if not existing_item:
        raise ClientResourcesNotFoundError(f"Project {project_id} not found")

    existing_project = Project(**existing_item)

    if user.role != UserRole.OWNER:
        raise ClientAuthorizationError("Only owners can update projects")

    if existing_project.group_id != user.group_id:
        raise ClientAuthorizationError(
            "You do not have access to this project",
        )

    if existing_project.version != expected_version:
        raise ClientConflictError(
            f"Version mismatch: expected {expected_version}, "
            f"current {existing_project.version}",
        )

    await validate_assignees_in_group(
        users_db=users_db,
        assigned_user_ids=assigned_user_ids,
        scenes=scenes,
        group_id=user.group_id,
    )

    merged_scenes = merge_scenes(
        existing_scenes=existing_project.scenes,
        scene_inputs=scenes,
    )

    updated_project = existing_project.model_copy(
        update={
            "project_name": project_name,
            "description": description,
            "assigned_user_ids": assigned_user_ids,
            "scenes": merged_scenes,
            "version": existing_project.version + 1,
            "updated_at": datetime.now(UTC).isoformat(),
        },
    )

    await projects_db.put_item(
        item=updated_project.model_dump(by_alias=True),
        condition_expression="version = :expected_version",
        expression_attribute_values={":expected_version": expected_version},
    )

    return updated_project
