# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Scene recording update domain logic."""

import logging
from datetime import UTC
from datetime import datetime
from uuid import uuid4

from recnavi.core.database.base_database import BaseDatabase
from recnavi.core.project.scene_urls import attach_scene_urls
from recnavi.core.storage.base_object_storage import BaseObjectStorage
from recnavi.core.types.project import Project
from recnavi.core.types.scene import SceneStatus
from recnavi.core.types.user import User
from recnavi.core.types.user import UserRole
from recnavi.exceptions.exceptions import ClientAuthorizationError
from recnavi.exceptions.exceptions import ClientConflictError
from recnavi.exceptions.exceptions import ClientNotFoundError


logger = logging.getLogger(__name__)


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
) -> Project:
    """Store a scene recording, then replace the previous shot.

    Returns the updated project with presigned playback URLs.

    The recording is uploaded under a new shot id, the scene is updated in
    DynamoDB, and only then is the previous shot deleted.
    """
    item = await projects_db.get_item(key={"projectId": project_id})
    if not item:
        raise ClientNotFoundError("Project not found")

    project = Project.model_validate(item)

    if not project.validate_permission(user=user, as_role=UserRole.STAFF):
        raise ClientAuthorizationError(
            "User does not have access permission to this project",
        )

    scene = next(
        (scene for scene in project.scenes if scene.scene_id == scene_id),
        None,
    )
    if scene is None:
        raise ClientNotFoundError("Scene not found")

    if user.user_id not in scene.assigned_user_ids:
        raise ClientAuthorizationError("Not assigned to this scene")

    old_video_key = scene.video_key
    shot_prefix = f"projects/{project_id}/scenes/{scene_id}"
    shot_id = str(uuid4())
    new_shot_prefix = f"{shot_prefix}/{shot_id}"
    video_key = f"{new_shot_prefix}.mp4"
    thumbnail_key = f"{new_shot_prefix}_thumb.jpg"

    previous_version = project.version

    scene.status = SceneStatus.PENDING
    scene.video_key = video_key
    scene.thumbnail_key = thumbnail_key
    scene.created_by = user.user_id
    scene.created_at = datetime.now(UTC).isoformat()

    project.update_scene(scene)

    try:
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
    except Exception:
        await _cleanup_new_shot(
            storage=storage,
            bucket_name=bucket_name,
            prefix=new_shot_prefix,
        )
        raise

    try:
        await projects_db.put_item(
            project.model_dump(by_alias=True),
            condition_expression=(
                "attribute_not_exists(version) OR version = :previous_version"
            ),
            expression_attribute_values={
                ":previous_version": previous_version,
            },
        )

    except ClientConflictError:
        await _cleanup_new_shot(
            storage=storage,
            bucket_name=bucket_name,
            prefix=new_shot_prefix,
        )
        raise

    if old_video_key:
        await storage.delete_object_by_key(
            bucket_name=bucket_name,
            object_key=old_video_key,
        )
        await storage.delete_object_by_key(
            bucket_name=bucket_name,
            object_key=old_video_key.removesuffix(".mp4") + "_thumb.jpg",
        )

    return await attach_scene_urls(
        storage=storage,
        bucket_name=bucket_name,
        project=project,
    )


async def _cleanup_new_shot(
    *,
    storage: BaseObjectStorage,
    bucket_name: str,
    prefix: str,
) -> None:
    """Delete partially uploaded or uncommitted recording objects."""
    try:
        await storage.delete_objects_by_prefix(
            bucket_name=bucket_name,
            prefix=prefix,
        )
    except Exception as e:
        logger.exception(
            f"Failed to clean up an uncommitted scene recording. {e!r}",
        )
