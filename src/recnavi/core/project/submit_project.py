# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Submit project for owner review."""

from datetime import UTC
from datetime import datetime

from recnavi.core.database.base_database import BaseDatabase
from recnavi.core.types.project import Project
from recnavi.core.types.project import ProjectStatus
from recnavi.core.types.scene import SceneStatus
from recnavi.core.types.user import User
from recnavi.core.types.user import UserRole
from recnavi.exceptions.exceptions import ClientAuthorizationError
from recnavi.exceptions.exceptions import ClientConflictError
from recnavi.exceptions.exceptions import ClientNotFoundError
from recnavi.exceptions.exceptions import ClientUnprocessableEntityError


async def submit_project(
    *,
    projects_db: BaseDatabase,
    project_id: str,
    user: User,
) -> tuple[Project, list[str]]:
    """Submit project for owner review.

    Staff report that shooting is done. A scene counts as unrecorded when
    its status is NOT_RECORDED or it has no video. Pending, rejected and
    approved scenes all count as recorded. The project becomes SUBMITTED
    only when no scene is unrecorded.
    """
    item = await projects_db.get_item(key={"projectId": project_id})

    if not item:
        raise ClientNotFoundError("Project not found")

    project = Project.model_validate(item)

    if user.group_id != project.group_id:
        raise ClientAuthorizationError(
            "Access to other group's project is forbidden",
        )

    if user.role != UserRole.STAFF:
        raise ClientAuthorizationError(
            "Only staff can submit a project",
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
        if scene.status == SceneStatus.NOT_RECORDED or scene.video_key is None
    ]

    should_submit = len(missing_scene_ids) == 0

    if should_submit:
        timestamp = datetime.now(UTC).isoformat()
        await projects_db.update_item(
            key={"projectId": project_id},
            update_expression="SET #status = :status, updatedAt = :updatedAt",
            expression_attribute_names={"#status": "status"},
            expression_attribute_values={
                ":status": ProjectStatus.SUBMITTED.value,
                ":updatedAt": timestamp,
            },
        )

        project.status = ProjectStatus.SUBMITTED
        project.updated_at = timestamp

    return (project, missing_scene_ids)
