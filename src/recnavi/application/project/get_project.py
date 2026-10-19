# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Application use case for getting a project."""

from recnavi.core.database.base_database import BaseDatabase
from recnavi.core.project.project import get_project
from recnavi.core.project.scene_urls import attach_scene_urls
from recnavi.core.storage.base_object_storage import BaseObjectStorage
from recnavi.core.types.project import Project
from recnavi.core.types.user import User


async def get_project_usecase(
    *,
    projects_db: BaseDatabase,
    storage: BaseObjectStorage,
    project_id: str,
    user: User,
) -> Project:
    """Get project if user is authorized."""
    project = await get_project(
        projects_db=projects_db,
        project_id=project_id,
        user=user,
    )
    return await attach_scene_urls(storage=storage, project=project)
