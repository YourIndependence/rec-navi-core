# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Notify the owner that a project was submitted."""

import logging

from recnavi.core.database.base_database import BaseDatabase
from recnavi.core.notification.base_notifier import BaseNotifier
from recnavi.core.types.project_view import ProjectView
from recnavi.core.types.user import User
from recnavi.exceptions.exceptions import NotificationSendError


logger = logging.getLogger(__name__)

REVIEW_PATH_TEMPLATE = "/projects/{project_id}/review"


def build_review_url(*, base_url: str, project_id: str) -> str:
    """Build the link to the review screen of a project."""
    path = REVIEW_PATH_TEMPLATE.format(project_id=project_id)
    return f"{base_url.rstrip('/')}{path}"


async def notify_project_submitted(
    *,
    users_db: BaseDatabase,
    notifier: BaseNotifier,
    project: ProjectView,
    submitter: User,
    base_url: str,
) -> bool:
    """Email the project owner that staff submitted the project.

    Best effort: a missing owner address or a delivery failure is logged and
    returns False. It never raises, so it cannot undo the submission.

    Returns:
        True if the notification was sent.

    """
    owner_item = await users_db.get_item(key={"userId": project.owner_user_id})
    owner_email = owner_item.get("email") if owner_item else None
    if not owner_email:
        logger.warning(
            "owner notification skipped: no email project_id=%s owner_user_id=%s",
            project.project_id,
            project.owner_user_id,
        )
        return False

    try:
        await notifier.send_project_submitted(
            to_email=owner_email,
            project_name=project.project_name,
            staff_name=submitter.user_name,
            review_url=build_review_url(
                base_url=base_url,
                project_id=project.project_id,
            ),
        )
    except NotificationSendError:
        logger.error(
            "owner notification failed project_id=%s owner_user_id=%s",
            project.project_id,
            project.owner_user_id,
            exc_info=True,
        )
        return False

    logger.info(
        "owner notification sent project_id=%s owner_user_id=%s",
        project.project_id,
        project.owner_user_id,
    )
    return True
