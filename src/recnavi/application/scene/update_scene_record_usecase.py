# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Update scene record use case."""

import uuid

from recnavi.core.database.base_database import BaseDatabase
from recnavi.core.scene.update_scene_record import update_scene_record
from recnavi.core.types.project import Project
from recnavi.core.types.user import User
from recnavi.infrastructure.s3.s3_client import delete_objects_by_prefix
from recnavi.infrastructure.s3.s3_client import upload_base64


async def update_scene_record_usecase(
    *,
    projects_db: BaseDatabase,
    project_id: str,
    scene_id: str,
    video_base64: str,
    thumbnail_base64: str,
    user: User,
    video_bucket_name: str,
) -> Project:
    """Upload scene recording to S3 and update DynamoDB.

    Args:
        projects_db: Database instance for projects table.
        project_id: Project ID.
        scene_id: Scene ID.
        video_base64: Base64-encoded video data.
        thumbnail_base64: Base64-encoded thumbnail data.
        user: Authenticated user.
        video_bucket_name: S3 bucket name for videos.

    Returns:
        Updated project with new scene recording.

    Raises:
        ClientNotFoundError: Project/scene not found.
        ClientAuthorizationError: Not authorized.
        ClientConflictError: Concurrent modification detected.

    """
    shot_id = str(uuid.uuid4())
    video_key = f"projects/{project_id}/scenes/{scene_id}/{shot_id}.mp4"
    thumbnail_key = (
        f"projects/{project_id}/scenes/{scene_id}/{shot_id}_thumb.jpg"
    )

    await upload_base64(
        bucket_name=video_bucket_name,
        object_key=video_key,
        base64_data=video_base64,
        content_type="video/mp4",
    )

    await upload_base64(
        bucket_name=video_bucket_name,
        object_key=thumbnail_key,
        base64_data=thumbnail_base64,
        content_type="image/jpeg",
    )

    async def delete_old_shot(prefix: str) -> None:
        await delete_objects_by_prefix(
            bucket_name=video_bucket_name,
            prefix=prefix,
        )

    return await update_scene_record(
        projects_db=projects_db,
        project_id=project_id,
        scene_id=scene_id,
        video_key=video_key,
        thumbnail_key=thumbnail_key,
        user=user,
        s3_delete_callback=delete_old_shot,
    )
