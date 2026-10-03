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
from uuid import uuid4

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
    """Merge scene inputs with existing scenes, preserving recording state."""
    existing_by_id = {scene.scene_id: scene for scene in existing_scenes}
    merged = []

    for scene_input in scene_inputs:
        if scene_input.scene_id is None:
            new_scene = Scene(
                scene_id=str(uuid4()),
                scene_principal=scene_input.scene_principal,
                assigned_user_ids=scene_input.assigned_user_ids,
                status=SceneStatus.NOT_RECORDED,
            )
            merged.append(new_scene)
        else:
            existing_scene = existing_by_id.get(scene_input.scene_id)
            if existing_scene:
                updated_scene = existing_scene.model_copy(
                    update={
                        "scene_principal": scene_input.scene_principal,
                        "assigned_user_ids": scene_input.assigned_user_ids,
                    },
                )
                merged.append(updated_scene)
            else:
                new_scene = Scene(
                    scene_id=scene_input.scene_id,
                    scene_principal=scene_input.scene_principal,
                    assigned_user_ids=scene_input.assigned_user_ids,
                    status=SceneStatus.NOT_RECORDED,
                )
                merged.append(new_scene)

    return merged


async def update_project(
    *,
    projects_db: BaseDatabase,
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

    if existing_project.version != expected_version:
        raise ClientConflictError(
            f"Version mismatch: expected {expected_version}, "
            f"current {existing_project.version}",
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
