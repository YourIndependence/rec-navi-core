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
from recnavi.core.project.scene_urls import attach_scene_urls
from recnavi.core.storage.base_object_storage import BaseObjectStorage
from recnavi.core.types.project import Project
from recnavi.core.types.project import ProjectStatus
from recnavi.core.types.user import User
from recnavi.core.types.user import UserRole
from recnavi.exceptions.exceptions import ClientAuthorizationError
from recnavi.exceptions.exceptions import ClientConflictError
from recnavi.exceptions.exceptions import ClientNotFoundError
from recnavi.exceptions.exceptions import ClientUnprocessableEntityError


async def submit_project(
    *,
    projects_db: BaseDatabase,
    storage: BaseObjectStorage,
    project_id: str,
    user: User,
) -> tuple[Project, list[str]]:
    """Accept completed shooting; report missing recordings and rejected scenes."""
    item = await projects_db.get_item(
        key={"projectId": project_id},
        consistent_read=True,
    )

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

    missing_scene_ids = project.get_missing_scene_ids()

    if not missing_scene_ids and project.status != ProjectStatus.SUBMITTED:
        previous_version = project.version
        project.status = ProjectStatus.SUBMITTED
        project.increment_version()
        try:
            await projects_db.put_item(
                item=project.model_dump(by_alias=True),
                condition_expression=(
                    "attribute_exists(projectId) AND "
                    "(attribute_not_exists(version) OR version = :previous_version)"
                ),
                expression_attribute_values={
                    ":previous_version": previous_version,
                },
            )
        except ClientConflictError:
            latest = await projects_db.get_item(
                key={"projectId": project_id},
                consistent_read=True,
            )
            if latest is None:
                raise
            latest_project = Project.model_validate(latest)
            if (
                latest_project.status != ProjectStatus.SUBMITTED
                or latest_project.group_id != user.group_id
                or user.user_id not in latest_project.assigned_user_ids
                or not latest_project.scenes
                or latest_project.get_missing_scene_ids()
            ):
                raise
            project = latest_project

    project_view = await attach_scene_urls(
        storage=storage,
        project=project,
    )

    return (project_view, missing_scene_ids)
