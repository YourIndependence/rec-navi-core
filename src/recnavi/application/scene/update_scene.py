# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Update scene use case."""

from recnavi.core.database.base_database import BaseDatabase
from recnavi.core.scene.update_scene import update_scene
from recnavi.core.storage.base_object_storage import BaseObjectStorage
from recnavi.core.types.project import Project
from recnavi.core.types.user import User


async def update_scene_usecase(
    *,
    projects_db: BaseDatabase,
    storage: BaseObjectStorage,
    project_id: str,
    scene_id: str,
    video_base64: str,
    thumbnail_base64: str,
    user: User,
) -> Project:
    """Store a scene recording and update the project."""
    return await update_scene(
        projects_db=projects_db,
        storage=storage,
        project_id=project_id,
        scene_id=scene_id,
        video_base64=video_base64,
        thumbnail_base64=thumbnail_base64,
        user=user,
    )
