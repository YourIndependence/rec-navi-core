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
from recnavi.core.scene.upsert_scene_master import update_scene_master
from recnavi.core.storage.base_object_storage import BaseObjectStorage
from recnavi.core.types.scene_master import SceneMaster


async def update_scene_master_usecase(
    *,
    scenes_db: BaseDatabase,
    scene_principal: str | None,
    title: str,
    max_duration_seconds: int,
    example_image: str | None,
    guide_image: str | None,
    bucket_name: str,
    storage: BaseObjectStorage,
) -> SceneMaster:
    """Create or update scene master with image upload."""
    scene_master = await update_scene_master(
        scenes_db=scenes_db,
        scene_principal=scene_principal,
        title=title,
        max_duration_seconds=max_duration_seconds,
        example_image=example_image,
        guide_image=guide_image,
        bucket_name=bucket_name,
        storage=storage,
    )

    return await scene_master.attach_presigned_url(storage=storage)
