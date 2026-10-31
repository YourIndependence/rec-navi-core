# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Notify the project owner that staff finished shooting."""

from recnavi.core.database.base_database import BaseDatabase
from recnavi.core.notification.base_notifier import BaseNotifier
from recnavi.core.types.project import Project
from recnavi.core.types.user import User
from recnavi.core.types.user import UserRole
from recnavi.exceptions.exceptions import ClientAuthorizationError
from recnavi.exceptions.exceptions import ClientNotFoundError
from recnavi.exceptions.exceptions import ClientUnprocessableEntityError


REVIEW_PATH_TEMPLATE = "/project/{project_id}"


def build_review_url(*, base_url: str, project_id: str) -> str:
    """Build the link to the review screen of a project."""
    path = REVIEW_PATH_TEMPLATE.format(project_id=project_id)
    return f"{base_url.rstrip('/')}{path}"


async def submit_project(
    *,
    projects_db: BaseDatabase,
    users_db: BaseDatabase,
    notifier: BaseNotifier,
    base_url: str,
    project_id: str,
    user: User,
) -> None:
    """Email the project owner that staff finished shooting.

    Raises:
        NotificationSendError: The email could not be delivered.

    """
    item = await projects_db.get_item(key={"projectId": project_id})
    if not item:
        raise ClientNotFoundError("Project not found")

    project = Project.model_validate(item)

    if not project.validate_permission(user=user, as_role=UserRole.STAFF):
        raise ClientAuthorizationError(
            "User does not have access permission to this project",
        )

    owner_item = await users_db.get_item(key={"userId": project.owner_user_id})
    owner = User.model_validate(owner_item) if owner_item else None
    owner_email = owner.email if owner else None
    if not owner_email:
        raise ClientUnprocessableEntityError("Owner has no email address")

    await notifier.send_project_submitted(
        to_email=owner_email,
        project_name=project.project_name,
        staff_name=user.user_name,
        review_url=build_review_url(
            base_url=base_url,
            project_id=project.project_id,
        ),
    )
