# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Review scene core logic."""

from recnavi.core.database.base_database import BaseDatabase
from recnavi.core.types.project import Project
from recnavi.core.types.scene import SceneStatus
from recnavi.core.types.user import User
from recnavi.core.types.user import UserRole
from recnavi.exceptions.exceptions import ClientAuthorizationError
from recnavi.exceptions.exceptions import ClientNotFoundError
from recnavi.exceptions.exceptions import ClientUnprocessableEntityError


async def review_scene(
    *,
    projects_db: BaseDatabase,
    project_id: str,
    scene_id: str,
    result: str,
    user: User,
) -> tuple[Project, int, SceneStatus]:
    """Review a scene recording (owner-only operation).

    Args:
        projects_db: Database instance for projects table.
        project_id: Project ID.
        scene_id: Scene ID.
        result: Review result ("approve" or "reject").
        user: Authenticated user (must be owner).

    Returns:
        Tuple of (project, scene_index, old_status).

    Raises:
        ClientAuthorizationError: User is not owner or different group.
        ClientNotFoundError: Project or scene not found.
        ClientUnprocessableEntityError: Invalid result value.

    """
    if result not in ("approve", "reject"):
        raise ClientUnprocessableEntityError(
            f"Invalid result value: {result}. Must be 'approve' or 'reject'.",
        )

    if user.role != UserRole.OWNER:
        raise ClientAuthorizationError("Only owners can review scenes")

    item = await projects_db.get_item(key={"projectId": project_id})
    if not item:
        raise ClientNotFoundError("Project not found")

    project = Project.model_validate(item)

    if project.group_id != user.group_id:
        raise ClientAuthorizationError(
            "Access to other group's project is forbidden",
        )

    scene_index = None
    old_status = None
    for i, s in enumerate(project.scenes):
        if s.scene_id == scene_id:
            scene_index = i
            old_status = s.status
            break

    if scene_index is None:
        raise ClientNotFoundError("Scene not found")

    return (project, scene_index, old_status)
