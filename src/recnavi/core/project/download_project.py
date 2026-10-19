# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Owner authorization for project downloads."""

from recnavi.core.storage.base_object_storage import BaseObjectStorage
from recnavi.core.types.project import Project
from recnavi.core.types.user import User
from recnavi.core.types.user import UserRole
from recnavi.exceptions.exceptions import ClientAuthorizationError


async def create_project_archive(
    *,
    user: User,
    project: Project,
    storage: BaseObjectStorage,
) -> Project:
    """Authorize the same-group owner before generating a download URL."""
    if user.group_id != project.group_id or not project.validate_permission(
        user=user,
        as_role=UserRole.OWNER,
    ):
        raise ClientAuthorizationError(
            "Only the project owner can download it.",
        )
    return await project.create_download_url(storage=storage)
