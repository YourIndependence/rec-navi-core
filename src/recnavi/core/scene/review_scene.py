# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Review scene core logic."""

from datetime import UTC
from datetime import datetime

from recnavi.core.database.base_database import BaseDatabase
from recnavi.core.project.scene_urls import attach_scene_urls
from recnavi.core.storage.base_object_storage import BaseObjectStorage
from recnavi.core.types.project import Project
from recnavi.core.types.project import ProjectStatus
from recnavi.core.types.project_view import ProjectView
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
    review_comment: str | None,
    user: User,
    storage: BaseObjectStorage,
    bucket_name: str,
) -> ProjectView:
    """Review a scene recording and return the project with presigned URLs."""
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

    scene_index = next(
        (i for i, s in enumerate(project.scenes) if s.scene_id == scene_id),
        None,
    )

    if scene_index is None:
        raise ClientNotFoundError("Scene not found")

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
        "#status",
        "#sceneStatus",
    )

    await projects_db.update_item(
        key={"projectId": project_id},
        update_expression=update_expression_with_names,
        condition_expression=f"scenes[{scene_index}].sceneId = :sceneId",
        expression_attribute_names=expression_attribute_names,
        expression_attribute_values=expression_values,
    )

    updated_item = await projects_db.get_item(key={"projectId": project_id})
    return await attach_scene_urls(
        storage=storage,
        bucket_name=bucket_name,
        project=Project.model_validate(updated_item),
    )
