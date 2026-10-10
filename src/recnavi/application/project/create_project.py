# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Create project use case."""

from recnavi.core.database.base_database import BaseDatabase
from recnavi.core.project.project_view import create_project_view
from recnavi.core.storage.base_object_storage import BaseObjectStorage
from recnavi.core.types.project_view import ProjectView
from recnavi.core.types.user import User


async def create_project_usecase(
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
    """Create a new project, save it and return it with playback URLs."""
    return await create_project_view(
        projects_db=projects_db,
        storage=storage,
        bucket_name=bucket_name,
        project_name=project_name,
        description=description,
        scene_principals=scene_principals,
        assigned_user_ids=assigned_user_ids,
        owner=owner,
    )
