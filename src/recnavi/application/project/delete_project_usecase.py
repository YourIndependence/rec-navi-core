# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Delete project use case."""

from recnavi.core.database.base_database import BaseDatabase
from recnavi.core.project.delete_project import delete_project
from recnavi.core.types.user import User
from recnavi.infrastructure.s3.s3_client import delete_objects_by_prefix


async def delete_project_usecase(
    *,
    projects_db: BaseDatabase,
    project_id: str,
    user: User,
    video_bucket_name: str,
) -> str:
    """Delete project from database and S3.

    Args:
        projects_db: Database instance for projects table.
        project_id: ID of project to delete.
        user: Authenticated user.
        video_bucket_name: S3 bucket name for videos.

    Returns:
        Deleted project ID.

    """
    deleted_project_id = await delete_project(
        projects_db=projects_db,
        project_id=project_id,
        user=user,
    )

    await delete_objects_by_prefix(
        bucket_name=video_bucket_name,
        prefix=f"projects/{project_id}/",
    )

    return deleted_project_id
