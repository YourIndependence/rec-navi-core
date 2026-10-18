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
from recnavi.core.types.scene import ReviewSceneResult
from recnavi.core.types.scene import SceneStatus
from recnavi.core.types.user import User
from recnavi.core.types.user import UserRole
from recnavi.exceptions.exceptions import ClientAuthorizationError
from recnavi.exceptions.exceptions import ClientNotFoundError


async def review_scene(
    *,
    projects_db: BaseDatabase,
    project_id: str,
    scene_id: str,
    result: ReviewSceneResult,
    review_comment: str | None,
    user: User,
    storage: BaseObjectStorage,
) -> Project:
    """Review a scene recording and return the project with presigned URLs."""
    item = await projects_db.get_item(key={"projectId": project_id})
    if not item:
        raise ClientNotFoundError("Project not found")

    project = Project.model_validate(item)

    if not project.validate_permission(user=user, as_role=UserRole.OWNER):
        raise ClientAuthorizationError(
            "User does not have access permission to this project",
        )

    scene_index = next(
        (i for i, s in enumerate(project.scenes) if s.scene_id == scene_id),
        None,
    )

    if scene_index is None:
        raise ClientNotFoundError("Scene not found")

    timestamp = datetime.now(UTC).isoformat()
    new_status = SceneStatus(result.value)

    scene = project.scenes[scene_index]
    scene.status = new_status
    scene.reviewed_by = user.user_id
    scene.reviewed_at = timestamp
    scene.review_comment = review_comment
    previous_version = project.version
    project.update_scene(scene)
    await projects_db.put_item(
        item=project.model_dump(by_alias=True),
        condition_expression=(
            "attribute_not_exists(version) OR version = :previous_version"
        ),
        expression_attribute_values={":previous_version": previous_version},
    )
    return await attach_scene_urls(
        storage=storage,
        project=project,
    )
