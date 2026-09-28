# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""List the projects visible to a group."""

from recnavi.core.database.base_database import BaseDatabase
from recnavi.core.project.projects import get_projects
from recnavi.core.types.project import Project


async def get_projects_usecase(
    *,
    projects_db: BaseDatabase,
    group_id: str,
    limit: int,
    cursor: str | None,
) -> tuple[list[Project], str | None]:
    """List the projects a group can see, newest first.

    Args:
        projects_db: Database instance for the projects table.
        group_id: Group identifier taken from the authenticated user.
        limit: Maximum items per page.
        cursor: Opaque pagination cursor from the previous response.

    Returns:
        Tuple of (projects, next_cursor). next_cursor is None on the last page.

    """
    return await get_projects(
        projects_db=projects_db,
        group_id=group_id,
        limit=limit,
        cursor=cursor,
    )
