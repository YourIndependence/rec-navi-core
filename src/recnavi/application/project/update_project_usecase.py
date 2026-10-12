# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Update project use case."""

from recnavi.core.database.base_database import BaseDatabase
from recnavi.core.project.update_project import update_project
from recnavi.core.storage.base_object_storage import BaseObjectStorage
from recnavi.core.types.project_view import ProjectView
from recnavi.core.types.scene_input import SceneInput
from recnavi.core.types.user import User


async def update_project_usecase(
    *,
    projects_db: BaseDatabase,
    users_db: BaseDatabase,
    project_id: str,
    project_name: str,
    description: str,
    assigned_user_ids: list[str],
    scenes: list[SceneInput],
    expected_version: int,
    user: User,
    storage: BaseObjectStorage,
    bucket_name: str,
) -> ProjectView:
    """Update project use case."""
    return await update_project(
        projects_db=projects_db,
        users_db=users_db,
        project_id=project_id,
        project_name=project_name,
        description=description,
        assigned_user_ids=assigned_user_ids,
        scenes=scenes,
        expected_version=expected_version,
        user=user,
        storage=storage,
        bucket_name=bucket_name,
    )
