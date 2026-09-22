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
) -> str:
    """Delete a project (owner-only operation).

    Args:
        projects_db: Database instance for projects table.
        project_id: ID of project to delete.
        user: Authenticated user attempting deletion.

    Returns:
        Deleted project ID.

    Raises:
        ClientNotFoundError: Project does not exist.
        ClientAuthorizationError: User is not owner or not same group.

    """
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

    return project_id
