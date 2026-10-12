# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Submit project use case."""

from recnavi.core.database.base_database import BaseDatabase
from recnavi.core.project.submit_project import submit_project
from recnavi.core.storage.base_object_storage import BaseObjectStorage
from recnavi.core.types.project_view import ProjectView
from recnavi.core.types.user import User


async def submit_project_usecase(
    *,
    projects_db: BaseDatabase,
    storage: BaseObjectStorage,
    bucket_name: str,
    project_id: str,
    user: User,
) -> tuple[ProjectView, list[str]]:
    """Submit project for owner review."""
    return await submit_project(
        projects_db=projects_db,
        storage=storage,
        bucket_name=bucket_name,
        project_id=project_id,
        user=user,
    )
