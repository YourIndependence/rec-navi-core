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
from recnavi.core.project.project_view import get_project_view
from recnavi.core.storage.base_object_storage import BaseObjectStorage
from recnavi.core.types.project_view import ProjectView
from recnavi.core.types.user import User


async def get_project_usecase(
    *,
    projects_db: BaseDatabase,
    storage: BaseObjectStorage,
    bucket_name: str,
    project_id: str,
    user: User,
) -> ProjectView:
    """Get project with playback URLs if user is authorized."""
    return await get_project_view(
        projects_db=projects_db,
        storage=storage,
        bucket_name=bucket_name,
        project_id=project_id,
        user=user,
    )
