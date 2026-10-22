# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Submit project use case."""

from recnavi.core.database.base_database import BaseDatabase
from recnavi.core.notification.base_notifier import BaseNotifier
from recnavi.core.project.submit_project import submit_project
from recnavi.core.types.user import User


async def submit_project_usecase(
    *,
    projects_db: BaseDatabase,
    users_db: BaseDatabase,
    notifier: BaseNotifier,
    base_url: str,
    project_id: str,
    user: User,
) -> None:
    """Notify the project owner that staff finished shooting."""
    return await submit_project(
        projects_db=projects_db,
        users_db=users_db,
        notifier=notifier,
        base_url=base_url,
        project_id=project_id,
        user=user,
    )
