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
from uuid import uuid4

from recnavi.core.database.base_database import BaseDatabase
from recnavi.core.project.scene_urls import attach_scene_urls
from recnavi.core.storage.base_object_storage import BaseObjectStorage
from recnavi.core.types.project import Project
from recnavi.core.types.project_view import ProjectView
from recnavi.core.types.scene import SceneStatus
from recnavi.core.types.user import User
from recnavi.core.types.user import UserRole
from recnavi.exceptions.exceptions import ClientAuthorizationError
from recnavi.exceptions.exceptions import ClientNotFoundError


async def update_scene_record(
    *,
    projects_db: BaseDatabase,
    storage: BaseObjectStorage,
    project_id: str,
    scene_id: str,
    video_base64: str,
    thumbnail_base64: str,
    user: User,
    bucket_name: str,
) -> ProjectView:
    """Store a scene recording, then replace the previous shot.

    Returns the updated project with presigned playback URLs.

    The recording is uploaded under a new shot id, the scene is updated in
    DynamoDB, and only then is the previous shot deleted.
    """
    if user.role != UserRole.STAFF:
        raise ClientAuthorizationError("Only staff can record scenes")

    item = await projects_db.get_item(key={"projectId": project_id})
    if not item:
        raise ClientNotFoundError("Project not found")

    project = Project.model_validate(item)

    if project.group_id != user.group_id:
        raise ClientAuthorizationError(
            "Access to other group's project is forbidden",
        )

    found = next(
        (
            (index, scene)
            for index, scene in enumerate(project.scenes)
            if scene.scene_id == scene_id
        ),
        None,
    )
    if found is None:
        raise ClientNotFoundError("Scene not found")
    scene_index, scene = found

    if user.user_id not in scene.assigned_user_ids:
        raise ClientAuthorizationError("Not assigned to this scene")

    shot_prefix = f"projects/{project_id}/scenes/{scene_id}"
    shot_id = str(uuid4())
    video_key = f"{shot_prefix}/{shot_id}.mp4"
    thumbnail_key = f"{shot_prefix}/{shot_id}_thumb.jpg"

    await storage.upload_base64(
        bucket_name=bucket_name,
        object_key=video_key,
        base64_data=video_base64,
        content_type="video/mp4",
    )
    await storage.upload_base64(
        bucket_name=bucket_name,
        object_key=thumbnail_key,
        base64_data=thumbnail_base64,
        content_type="image/jpeg",
    )

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
            ":createdAt": datetime.now(UTC).isoformat(),
            ":sceneId": scene_id,
        },
    )

    if scene.video_key:
        old_shot_id = scene.video_key.rsplit("/", 1)[-1].removesuffix(".mp4")
        await storage.delete_objects_by_prefix(
            bucket_name=bucket_name,
            prefix=f"{shot_prefix}/{old_shot_id}",
        )

    updated_item = await projects_db.get_item(key={"projectId": project_id})
    return await attach_scene_urls(
        storage=storage,
        bucket_name=bucket_name,
        project=Project.model_validate(updated_item),
    )
