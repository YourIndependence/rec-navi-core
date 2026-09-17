# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Core business logic for project operations."""

from recnavi.core.database.base_database import BaseDatabase
from recnavi.core.types.project import Project
from recnavi.core.types.user import User
from recnavi.exceptions.exceptions import ClientAuthorizationError
from recnavi.exceptions.exceptions import ClientNotFoundError


async def get_project_if_authorized(
    projects_db: BaseDatabase,
    project_id: str,
    user: User,
) -> Project:
    """Get project if user is authorized (owner or assigned staff).

    Authorization rules:
    - User must belong to the same group as the project
    - User must be either the owner or assigned staff

    Args:
        projects_db: Database instance for projects table.
        project_id: Project ID to retrieve.
        user: Authenticated user requesting the project.

    Returns:
        Project object with all scenes.

    Raises:
        ClientNotFoundError: Project does not exist (404).
        ClientAuthorizationError: User not authorized (403).

    """
    item = await projects_db.get_item(key={"projectId": project_id})

    if not item:
        raise ClientNotFoundError("Project not found")

    project = Project.model_validate(item)

    # Group membership check (403 for other groups)
    if project.group_id != user.group_id:
        raise ClientAuthorizationError(
            "Access to other group's project is forbidden",
        )

    # Owner or assigned staff check
    is_owner = project.owner_user_id == user.user_id
    is_assigned_staff = user.user_id in project.assigned_user_ids

    if not (is_owner or is_assigned_staff):
        raise ClientAuthorizationError(
            "User is not the owner or assigned staff for this project",
        )

    return project
