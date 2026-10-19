# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Scene master domain logic."""

from recnavi.core.database.base_database import BaseDatabase
from recnavi.core.storage.base_object_storage import BaseObjectStorage
from recnavi.core.storage.image_urls import generate_image_url
from recnavi.core.types.scene_master import SceneMaster
from recnavi.core.types.scene_master import SceneMasterView


async def get_scene_masters(scenes_db: BaseDatabase) -> list[SceneMaster]:
    """Retrieve all scene masters from the database."""
    result = await scenes_db.scan()

    return [SceneMaster.model_validate(item) for item in result.items]


async def attach_scene_master_urls(
    *,
    scenes: list[SceneMaster],
    storage: BaseObjectStorage,
) -> list[SceneMasterView]:
    """Replace master image references with temporary URLs."""
    return [
        SceneMasterView(
            scene_principal=scene.scene_principal,
            title=scene.title,
            max_duration_seconds=scene.max_duration_seconds,
            thumbnail_url=await generate_image_url(
                storage=storage,
                image_uri=scene.thumbnail_uri,
            ),
            guide_url=await generate_image_url(
                storage=storage,
                image_uri=scene.guide_uri,
            ),
        )
        for scene in scenes
    ]
