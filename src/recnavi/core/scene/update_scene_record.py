# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Scene recording update domain logic."""

from datetime import UTC
from datetime import datetime

from recnavi.core.database.base_database import BaseDatabase
from recnavi.core.types.project import Project
from recnavi.core.types.scene import SceneStatus
from recnavi.core.types.user import User
from recnavi.exceptions.exceptions import ClientAuthorizationError
from recnavi.exceptions.exceptions import ClientNotFoundError


async def update_scene_record(
    *,
    projects_db: BaseDatabase,
    project_id: str,
    scene_id: str,
    video_key: str,
    thumbnail_key: str,
    user: User,
    s3_delete_callback=None,
) -> Project:
    """Update scene recording in DynamoDB after S3 upload.

    Args:
        projects_db: Database instance for projects table.
        project_id: ID of project containing the scene.
        scene_id: ID of scene to update.
        video_key: S3 key for uploaded video.
        thumbnail_key: S3 key for uploaded thumbnail.
        user: Authenticated user (must be assigned staff).
        s3_delete_callback: Optional async callback to delete old S3 objects.

    Returns:
        Updated project.

    Raises:
        ClientNotFoundError: Project or scene not found.
        ClientAuthorizationError: User not in same group or not assigned to scene.
        ClientConflictError: Concurrent modification detected.

    """
    item = await projects_db.get_item(key={"projectId": project_id})
    if not item:
        raise ClientNotFoundError("Project not found")

    project = Project.model_validate(item)

    if project.group_id != user.group_id:
        raise ClientAuthorizationError(
            "Access to other group's project is forbidden",
        )

    scene_index = None
    scene = None
    for i, s in enumerate(project.scenes):
        if s.scene_id == scene_id:
            scene_index = i
            scene = s
            break

    if scene is None:
        raise ClientNotFoundError("Scene not found")

    if user.user_id not in scene.assigned_user_ids:
        raise ClientAuthorizationError("Not assigned to this scene")

    old_video_key = scene.video_key
    timestamp = datetime.now(UTC).isoformat()

    await projects_db.update_item(
        key={"projectId": project_id},
        update_expression=(
            f"SET scenes[{scene_index}].#sceneStatus = :status, "
            f"scenes[{scene_index}].videoKey = :videoKey, "
            f"scenes[{scene_index}].thumbnailKey = :thumbnailKey, "
            f"scenes[{scene_index}].createdBy = :createdBy, "
            f"scenes[{scene_index}].createdAt = :createdAt"
        ),
        condition_expression=f"scenes[{scene_index}].sceneId = :sceneId",
        expression_attribute_names={"#sceneStatus": "status"},
        expression_attribute_values={
            ":status": SceneStatus.PENDING.value,
            ":videoKey": video_key,
            ":thumbnailKey": thumbnail_key,
            ":createdBy": user.user_id,
            ":createdAt": timestamp,
            ":sceneId": scene_id,
        },
    )

    if old_video_key and s3_delete_callback:
        old_shot_id = old_video_key.split("/")[-1].replace(".mp4", "")
        old_key_prefix = (
            f"projects/{project_id}/scenes/{scene_id}/{old_shot_id}"
        )
        await s3_delete_callback(old_key_prefix)

    updated_item = await projects_db.get_item(key={"projectId": project_id})
    return Project.model_validate(updated_item)
