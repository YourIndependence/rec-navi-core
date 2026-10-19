# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Update project with optimistic locking."""

from recnavi.core.database.base_database import BaseDatabase
from recnavi.core.project.scene_urls import attach_scene_urls
from recnavi.core.storage.base_object_storage import BaseObjectStorage
from recnavi.core.types.project import Project
from recnavi.core.types.scene import Scene
from recnavi.core.types.user import User
from recnavi.core.types.user import UserRole
from recnavi.exceptions.exceptions import ClientAuthorizationError
from recnavi.exceptions.exceptions import ClientConflictError
from recnavi.exceptions.exceptions import ClientNotFoundError


async def update_project(
    *,
    projects_db: BaseDatabase,
    project_id: str,
    project_name: str,
    description: str,
    assigned_user_ids: list[str],
    scenes: list[Scene],
    expected_version: int,
    user: User,
    storage: BaseObjectStorage,
) -> Project:
    """Update project with optimistic locking."""
    item = await projects_db.get_item(key={"projectId": project_id})
    if not item:
        raise ClientNotFoundError("Project not found")

    project = Project.model_validate(item)

    if not project.validate_permission(user=user, as_role=UserRole.OWNER):
        raise ClientAuthorizationError(
            "User does not have access permission to this project",
        )

    if project.version != expected_version:
        raise ClientConflictError(
            f"Version mismatch: expected {expected_version}, "
            f"current {project.version}",
        )

    project.scenes = scenes
    project.project_name = project_name
    project.description = description
    project.assigned_user_ids = assigned_user_ids
    project.increment_version()

    await projects_db.put_item(
        item=project.to_storage_item(),
        condition_expression="version = :expected_version",
        expression_attribute_values={":expected_version": expected_version},
    )

    return await attach_scene_urls(
        storage=storage,
        project=project,
    )
