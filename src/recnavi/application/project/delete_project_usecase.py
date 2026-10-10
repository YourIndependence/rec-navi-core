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
from recnavi.core.storage.base_object_storage import BaseObjectStorage
from recnavi.core.types.user import User


async def delete_project_usecase(
    *,
    projects_db: BaseDatabase,
    project_id: str,
    user: User,
    storage: BaseObjectStorage,
    media_bucket_name: str,
) -> str:
    """Delete project from database and object storage."""
    return await delete_project(
        projects_db=projects_db,
        project_id=project_id,
        user=user,
        storage=storage,
        bucket_name=media_bucket_name,
    )
