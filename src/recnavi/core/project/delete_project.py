# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Project deletion domain logic."""

from recnavi.core.database.base_database import BaseDatabase
from recnavi.core.storage.base_object_storage import BaseObjectStorage
from recnavi.core.types.project import Project
from recnavi.core.types.user import User
from recnavi.core.types.user import UserRole
from recnavi.exceptions.exceptions import ClientAuthorizationError
from recnavi.exceptions.exceptions import ClientNotFoundError


async def delete_project(
    *,
    projects_db: BaseDatabase,
    project_id: str,
    user: User,
    storage: BaseObjectStorage,
    bucket_name: str,
) -> str:
    """Delete a project and its stored media (owner-only operation)."""
    if user.role != UserRole.OWNER:
        raise ClientAuthorizationError("Only owners can delete projects")

    item = await projects_db.get_item(key={"projectId": project_id})

    if not item:
        raise ClientNotFoundError("Project not found")

    project = Project.model_validate(item)

    if project.group_id != user.group_id:
        raise ClientAuthorizationError(
            "Access to other group's project is forbidden",
        )

    await projects_db.delete_item(key={"projectId": project_id})
    await storage.delete_objects_by_prefix(
        bucket_name=bucket_name,
        prefix=f"projects/{project_id}/",
    )

    return project_id
