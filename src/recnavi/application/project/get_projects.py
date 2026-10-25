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
from recnavi.core.metrics.base_metrics_publisher import BaseMetricsPublisher
from recnavi.core.project.projects import get_projects
from recnavi.core.storage.base_object_storage import BaseObjectStorage
from recnavi.core.types.project import Project


async def get_projects_usecase(
    *,
    projects_db: BaseDatabase,
    storage: BaseObjectStorage,
    user_id: str,
    group_id: str,
    limit: int = 64,
    cursor: str | None,
    metrics: BaseMetricsPublisher | None = None,
) -> tuple[list[Project], str | None]:
    """List the projects a group can see, newest first.

    Returns:
        Tuple of (projects, next_cursor). next_cursor is None on the last page.

    """
    projects, next_cursor = await get_projects(
        projects_db=projects_db,
        user_id=user_id,
        group_id=group_id,
        limit=limit,
        cursor=cursor,
        metrics=metrics,
    )
    return (
        [
            await project.attach_presigned_url(storage=storage)
            for project in projects
        ],
        next_cursor,
    )
