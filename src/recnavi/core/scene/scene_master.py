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
from recnavi.core.types.scene_master import SceneMaster


async def get_scene_masters(scenes_db: BaseDatabase) -> list[SceneMaster]:
    """Retrieve all scene masters from the database."""
    result = await scenes_db.scan()

    return [SceneMaster.model_validate(item) for item in result.items]


async def attach_scene_master_urls(
    *,
    scenes: list[SceneMaster],
    storage: BaseObjectStorage,
) -> list[SceneMaster]:
    """Replace master image references with temporary URLs."""
    return [
        await scene.attach_presigned_url(storage=storage) for scene in scenes
    ]
