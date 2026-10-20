# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Update scene master use case."""

from recnavi.core.database.base_database import BaseDatabase
from recnavi.core.scene.update_scene_master import update_scene_master
from recnavi.core.storage.base_object_storage import BaseObjectStorage
from recnavi.core.types.scene_master import SceneMaster
from recnavi.core.types.user import User


async def update_scene_master_usecase(
    *,
    scenes_db: BaseDatabase,
    storage: BaseObjectStorage,
    user: User,
    scene_principal: str,
    title: str | None = None,
    max_duration_seconds: int | None = None,
    thumbnail_image: str | None,
    guide_image: str | None,
) -> SceneMaster:
    """Create or update scene master with image upload."""
    scene_master = await update_scene_master(
        scenes_db=scenes_db,
        storage=storage,
        user=user,
        scene_principal=scene_principal,
        title=title,
        max_duration_seconds=max_duration_seconds,
        thumbnail_image=thumbnail_image,
        guide_image=guide_image,
    )

    return await scene_master.attach_presigned_url(storage=storage)
