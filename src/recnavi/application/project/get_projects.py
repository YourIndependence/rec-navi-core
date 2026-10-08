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
from recnavi.infrastructure.cloudwatch.cloudwatch_metrics import (
    put_filter_metrics,
)


async def get_projects_usecase(
    *,
    projects_db: BaseDatabase,
    user_id: str,
    group_id: str,
    limit: int = 64,
    cursor: str | None,
) -> tuple[list[Project], str | None]:
    """List the projects a group can see, newest first.

    Returns:
        Tuple of (projects, next_cursor). next_cursor is None on the last page.

    """
    return await get_projects(
        projects_db=projects_db,
        user_id=user_id,
        group_id=group_id,
        limit=limit,
        cursor=cursor,
        record_metrics=put_filter_metrics,
    )
