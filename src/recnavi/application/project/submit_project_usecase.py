# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Submit project use case."""

from datetime import UTC
from datetime import datetime

from recnavi.core.database.base_database import BaseDatabase
from recnavi.core.project.submit_project import submit_project
from recnavi.core.types.project import Project
from recnavi.core.types.project import ProjectStatus
from recnavi.core.types.user import User


async def submit_project_usecase(
    *,
    projects_db: BaseDatabase,
    project_id: str,
    user: User,
) -> tuple[Project, list[str]]:
    """Submit project for owner review.

    Args:
        projects_db: Projects database.
        project_id: Project ID to submit.
        user: User submitting the project.

    Returns:
        Tuple of (updated_project, missing_scene_ids).
        - updated_project: Project with SUBMITTED status if all approved
        - missing_scene_ids: IDs of scenes not approved (empty if all approved)

    Raises:
        ClientNotFoundError: Project not found.
        ClientAuthorizationError: User not authorized.
        ClientUnprocessableEntityError: Project has no scenes.
        ClientConflictError: Project already submitted.

    """
    project, missing_scene_ids, should_submit = await submit_project(
        projects_db=projects_db,
        project_id=project_id,
        user=user,
    )

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

        updated_item = await projects_db.get_item(
            key={"projectId": project_id},
        )
        updated_project = Project.model_validate(updated_item)
        return (updated_project, missing_scene_ids)

    return (project, missing_scene_ids)
