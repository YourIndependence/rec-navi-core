# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Review scene use case."""

from datetime import UTC
from datetime import datetime

from recnavi.core.database.base_database import BaseDatabase
from recnavi.core.scene.review_scene import review_scene
from recnavi.core.types.project import Project
from recnavi.core.types.project import ProjectStatus
from recnavi.core.types.scene import SceneStatus
from recnavi.core.types.user import User


async def review_scene_usecase(
    *,
    projects_db: BaseDatabase,
    project_id: str,
    scene_id: str,
    result: str,
    review_comment: str | None,
    user: User,
) -> Project:
    """Review a scene recording (approve or reject).

    Args:
        projects_db: Database instance for projects table.
        project_id: Project ID.
        scene_id: Scene ID.
        result: Review result ("approve" or "reject").
        review_comment: Optional review comment.
        user: Authenticated user (must be owner).

    Returns:
        Updated project with reviewed scene.

    Raises:
        ClientAuthorizationError: User is not owner or different group.
        ClientNotFoundError: Project or scene not found.
        ClientUnprocessableEntityError: Invalid result value.
        ClientConflictError: Concurrent modification detected.

    """
    project, scene_index, _old_status = await review_scene(
        projects_db=projects_db,
        project_id=project_id,
        scene_id=scene_id,
        result=result,
        user=user,
    )

    timestamp = datetime.now(UTC).isoformat()
    new_status = (
        SceneStatus.APPROVE if result == "approve" else SceneStatus.REJECT
    )

    update_expressions = [
        f"scenes[{scene_index}].#status = :status",
        f"scenes[{scene_index}].reviewedBy = :reviewedBy",
        f"scenes[{scene_index}].reviewedAt = :reviewedAt",
    ]

    expression_values = {
        ":status": new_status.value,
        ":reviewedBy": user.user_id,
        ":reviewedAt": timestamp,
        ":sceneId": scene_id,
    }

    if review_comment is not None:
        update_expressions.append(
            f"scenes[{scene_index}].reviewComment = :reviewComment",
        )
        expression_values[":reviewComment"] = review_comment

    expression_attribute_names = {"#sceneStatus": "status"}

    if result == "reject" and project.status == ProjectStatus.SUBMITTED:
        update_expressions.append("#projectStatus = :projectStatus")
        expression_attribute_names["#projectStatus"] = "status"
        expression_values[":projectStatus"] = ProjectStatus.IN_PROGRESS.value

    update_expression_with_names = "SET " + ", ".join(update_expressions)
    update_expression_with_names = update_expression_with_names.replace(
        "#status", "#sceneStatus",
    )

    await projects_db.update_item(
        key={"projectId": project_id},
        update_expression=update_expression_with_names,
        condition_expression=f"scenes[{scene_index}].sceneId = :sceneId",
        expression_attribute_names=expression_attribute_names,
        expression_attribute_values=expression_values,
    )

    updated_item = await projects_db.get_item(key={"projectId": project_id})
    return Project.model_validate(updated_item)
