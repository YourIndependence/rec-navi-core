# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""List the scene masters available to the CMS."""

from recnavi.core.database.base_database import BaseDatabase
from recnavi.core.scene.scene_master import attach_scene_master_urls
from recnavi.core.scene.scene_master import get_scene_masters
from recnavi.core.storage.base_object_storage import BaseObjectStorage
from recnavi.core.types.scene_master import SceneMasterView


async def get_scene_masters_usecase(
    *,
    scenes_db: BaseDatabase,
    storage: BaseObjectStorage,
) -> list[SceneMasterView]:
    """List scene masters with temporary image URLs."""
    scenes = await get_scene_masters(scenes_db=scenes_db)
    return await attach_scene_master_urls(scenes=scenes, storage=storage)
