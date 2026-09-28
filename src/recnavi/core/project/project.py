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
from recnavi.exceptions.exceptions import ClientResourcesNotFoundError


async def get_project(
    *,
    projects_db: BaseDatabase,
    project_id: str,
    user: User,
) -> Project:
    """Get project if user is authorized."""
    item = await projects_db.get_item(key={"projectId": project_id})

    if not item:
        raise ClientResourcesNotFoundError("Project not found")

    project = Project.model_validate(item)

    if project.is_accessible(user=user):
        return project

    raise ClientAuthorizationError(
        "User does not have access to this project",
    )
