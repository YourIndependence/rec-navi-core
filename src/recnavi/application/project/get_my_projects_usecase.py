# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""List the projects assigned to the authenticated user."""

from recnavi.core.database.base_database import BaseDatabase
from recnavi.core.project.projects import get_my_projects
from recnavi.core.types.project import Project


async def get_my_projects_usecase(
    *,
    projects_db: BaseDatabase,
    group_id: str,
    user_id: str,
    limit: int,
    cursor: str | None,
) -> tuple[list[Project], str | None]:
    """List projects assigned to the authenticated user, newest first."""
    return await get_my_projects(
        projects_db=projects_db,
        group_id=group_id,
        user_id=user_id,
        limit=limit,
        cursor=cursor,
    )
