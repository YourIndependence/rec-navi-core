# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Notify project submitted use case."""

from recnavi.core.database.base_database import BaseDatabase
from recnavi.core.notification.base_notifier import BaseNotifier
from recnavi.core.project.notify_project_submitted import (
    notify_project_submitted,
)
from recnavi.core.types.project_view import ProjectView
from recnavi.core.types.user import User


async def notify_project_submitted_usecase(
    *,
    users_db: BaseDatabase,
    notifier: BaseNotifier,
    project: ProjectView,
    submitter: User,
    base_url: str,
) -> bool:
    """Notify the owner that the project was submitted."""
    return await notify_project_submitted(
        users_db=users_db,
        notifier=notifier,
        project=project,
        submitter=submitter,
        base_url=base_url,
    )
