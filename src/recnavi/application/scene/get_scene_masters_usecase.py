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
from recnavi.core.scene.scene_master import get_scene_masters
from recnavi.core.types.scene_master import SceneMaster


async def get_scene_masters_usecase(
    *,
    scenes_db: BaseDatabase,
) -> list[SceneMaster]:
    """List every scene master.

    Args:
        scenes_db: Database instance for the scenes table.

    Returns:
        All scene masters stored in the scenes table.

    """
    return await get_scene_masters(scenes_db=scenes_db)
