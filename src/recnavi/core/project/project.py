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
    """Get project if user is authorized."""
    item = await projects_db.get_item(key={"projectId": project_id})

    if not item:
        raise ClientNotFoundError("Project not found")

    project = Project.model_validate(item)

    if project.group_id != user.group_id:
        raise ClientAuthorizationError(
            "Access to other group's project is forbidden",
        )

    is_owner = project.owner_user_id == user.user_id
    is_assigned_staff = user.user_id in project.assigned_user_ids

    if not (is_owner or is_assigned_staff):
        raise ClientAuthorizationError(
            "User is not the owner or assigned staff for this project",
        )

    return project
