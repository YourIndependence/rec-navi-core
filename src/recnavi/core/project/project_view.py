# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Build client-facing project views with presigned scene URLs."""

from recnavi.core.database.base_database import BaseDatabase
from recnavi.core.project.create_project import create_project
from recnavi.core.project.project import get_project
from recnavi.core.project.scene_urls import attach_scene_urls
from recnavi.core.storage.base_object_storage import BaseObjectStorage
from recnavi.core.types.project_view import ProjectView
from recnavi.core.types.user import User


async def get_project_view(
    *,
    projects_db: BaseDatabase,
    storage: BaseObjectStorage,
    bucket_name: str,
    project_id: str,
    user: User,
) -> ProjectView:
    """Get an accessible project with presigned scene URLs."""
    project = await get_project(
        projects_db=projects_db,
        project_id=project_id,
        user=user,
    )
    return await attach_scene_urls(
        storage=storage,
        bucket_name=bucket_name,
        project=project,
    )


async def create_project_view(
    *,
    projects_db: BaseDatabase,
    storage: BaseObjectStorage,
    bucket_name: str,
    project_name: str,
    description: str,
    scene_principals: list[str],
    assigned_user_ids: list[str],
    owner: User,
) -> ProjectView:
    """Create a project and return it with presigned scene URLs."""
    project = await create_project(
        projects_db=projects_db,
        project_name=project_name,
        description=description,
        scene_principals=scene_principals,
        assigned_user_ids=assigned_user_ids,
        owner=owner,
    )
    return await attach_scene_urls(
        storage=storage,
        bucket_name=bucket_name,
        project=project,
    )
