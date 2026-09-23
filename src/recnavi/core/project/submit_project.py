# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Submit project for owner review."""

from recnavi.core.database.base_database import BaseDatabase
from recnavi.core.types.project import Project
from recnavi.core.types.project import ProjectStatus
from recnavi.core.types.scene import SceneStatus
from recnavi.core.types.user import User
from recnavi.exceptions.exceptions import ClientAuthorizationError
from recnavi.exceptions.exceptions import ClientConflictError
from recnavi.exceptions.exceptions import ClientNotFoundError
from recnavi.exceptions.exceptions import ClientUnprocessableEntityError


async def submit_project(
    *,
    projects_db: BaseDatabase,
    project_id: str,
    user: User,
) -> tuple[Project, list[str], bool]:
    """Check if project is ready for submission.

    Args:
        projects_db: Projects database.
        project_id: Project ID to submit.
        user: User submitting the project.

    Returns:
        Tuple of (project, missing_scene_ids, should_submit).
        - project: Current project state
        - missing_scene_ids: IDs of scenes not approved
        - should_submit: True if all scenes approved

    Raises:
        ClientNotFoundError: Project not found.
        ClientAuthorizationError: User not in assigned_user_ids.
        ClientUnprocessableEntityError: Project has no scenes.
        ClientConflictError: Project already submitted.

    """
    item = await projects_db.get_item(key={"projectId": project_id})

    if not item:
        raise ClientNotFoundError("Project not found")

    project = Project.model_validate(item)

    if user.group_id != project.group_id:
        raise ClientAuthorizationError(
            "Access to other group's project is forbidden",
        )

    if user.user_id not in project.assigned_user_ids:
        raise ClientAuthorizationError(
            "User is not assigned to this project",
        )

    if not project.scenes:
        raise ClientUnprocessableEntityError(
            "Cannot submit project with no scenes",
        )

    if project.status == ProjectStatus.SUBMITTED:
        raise ClientConflictError(
            "Project already submitted",
        )

    missing_scene_ids = [
        scene.scene_id
        for scene in project.scenes
        if scene.status != SceneStatus.APPROVE
    ]

    should_submit = len(missing_scene_ids) == 0

    return (project, missing_scene_ids, should_submit)
