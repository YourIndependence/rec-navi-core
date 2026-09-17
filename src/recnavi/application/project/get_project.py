# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Application use case for getting a project with presigned URLs."""

from recnavi.apis.schemas.project_schemas import ProjectView
from recnavi.apis.schemas.project_schemas import SceneView
from recnavi.core.database.base_database import BaseDatabase
from recnavi.core.project.project import get_project_if_authorized
from recnavi.core.types.user import User
from recnavi.infrastructure.s3.s3_client import generate_presigned_url


async def get_project_use_case(
    projects_db: BaseDatabase,
    project_id: str,
    user: User,
    video_bucket_name: str,
) -> ProjectView:
    """Get project with presigned URLs for videos and thumbnails.

    Args:
        projects_db: Database instance for projects table.
        project_id: Project ID to retrieve.
        user: Authenticated user requesting the project.
        video_bucket_name: S3 bucket name for video/thumbnail storage.

    Returns:
        ProjectView with SceneView objects containing presigned URLs.

    Raises:
        ClientNotFoundError: Project does not exist (404).
        ClientAuthorizationError: User not authorized (403).

    """
    # Core layer: get project with authorization check
    project = await get_project_if_authorized(
        projects_db=projects_db,
        project_id=project_id,
        user=user,
    )

    # Infrastructure layer: resolve presigned URLs for each scene
    scene_views = []
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

        scene_views.append(
            SceneView(
                scene_id=scene.scene_id,
                scene_principal=scene.scene_principal,
                status=scene.status.value,
                video_url=video_url,
                thumbnail_url=thumbnail_url,
                created_by=scene.created_by,
                created_at=scene.created_at,
                assigned_at=scene.assigned_at,
                assigned_user_ids=scene.assigned_user_ids,
            ),
        )

    return ProjectView(
        project_id=project.project_id,
        group_id=project.group_id,
        project_name=project.project_name,
        description=project.description,
        owner_user_id=project.owner_user_id,
        assigned_user_ids=project.assigned_user_ids,
        created_at=project.created_at,
        updated_at=project.updated_at,
        status=project.status,
        version=project.version,
        scenes=scene_views,
    )
