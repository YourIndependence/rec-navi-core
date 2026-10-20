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
    user: User,
    scene_principal: str,
    title: str | None = None,
    max_duration_seconds: int | None = None,
    example_image: str | None,
    guide_image: str | None,
    storage: BaseObjectStorage,
) -> SceneMaster:
    """Create or update scene master with image upload."""
    scene_master = await update_scene_master(
        scenes_db=scenes_db,
        user=user,
        scene_principal=scene_principal,
        title=title,
        max_duration_seconds=max_duration_seconds,
        example_image=example_image,
        guide_image=guide_image,
        storage=storage,
    )

    return await scene_master.attach_presigned_url(storage=storage)
