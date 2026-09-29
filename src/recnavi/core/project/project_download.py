# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Project download validation logic."""

from recnavi.core.types.project import Project
from recnavi.core.types.scene import SceneStatus
from recnavi.core.types.user import User
from recnavi.core.types.user import UserRole
from recnavi.exceptions.exceptions import ClientAuthorizationError
from recnavi.exceptions.exceptions import ClientUnprocessableEntityError


def validate_project_for_download(
    *,
    user: User,
    project: Project,
) -> None:
    """Validate project download eligibility.

    Args:
        user: Authenticated user.
        project: Project to download.

    Raises:
        ClientAuthorizationError: User is not owner or wrong group.
        ClientUnprocessableEntityError: Project has no scenes or not all approved.

    """
    if user.role != UserRole.OWNER:
        raise ClientAuthorizationError("forbidden")

    if user.group_id != project.group_id:
        raise ClientAuthorizationError("forbidden")

    if not project.scenes:
        raise ClientUnprocessableEntityError(
            "Project has no scenes. Cannot create archive.",
        )

    unapproved_scenes = [
        scene
        for scene in project.scenes
        if scene.status != SceneStatus.APPROVE
    ]
    if unapproved_scenes:
        unapproved_ids = [scene.scene_id for scene in unapproved_scenes]
        raise ClientUnprocessableEntityError(
            f"Not all scenes are approved. Unapproved scenes: {unapproved_ids}",
        )
