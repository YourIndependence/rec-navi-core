# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Application use case for getting a project with presigned URLs."""

from recnavi.core.database.base_database import BaseDatabase
from recnavi.core.project.project import get_project_if_authorized
from recnavi.core.types.project import Project
from recnavi.core.types.user import User
from recnavi.infrastructure.s3.s3_client import generate_presigned_url


async def get_project_use_case(
    projects_db: BaseDatabase,
    project_id: str,
    user: User,
    video_bucket_name: str,
) -> tuple[Project, dict[str, dict[str, str | None]]]:
    """Get project with presigned URLs for videos and thumbnails."""
    project = await get_project_if_authorized(
        projects_db=projects_db,
        project_id=project_id,
        user=user,
    )

    scene_urls: dict[str, dict[str, str | None]] = {}
    for scene in project.scenes:
        video_url = None
        thumbnail_url = None

        if scene.video_key:
            video_url = await generate_presigned_url(
                bucket_name=video_bucket_name,
                object_key=scene.video_key,
            )

        if scene.thumbnail_key:
            thumbnail_url = await generate_presigned_url(
                bucket_name=video_bucket_name,
                object_key=scene.thumbnail_key,
            )

        scene_urls[scene.scene_id] = {
            "video_url": video_url,
            "thumbnail_url": thumbnail_url,
        }

    return project, scene_urls
