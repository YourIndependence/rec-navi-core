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
from recnavi.core.types.scene_master import SceneMaster


async def get_scene_masters(scenes_db: BaseDatabase) -> list[SceneMaster]:
    """Retrieve all scene masters from the database.

    This performs a full table scan. The scenes table is small (dozens of rows,
    shared across all tenants), so a scan is acceptable here.

    Args:
        scenes_db: Database instance for the scenes table.

    Returns:
        List of all scene masters. Empty list if no scenes exist.

    """
    result = await scenes_db.scan()

    return [SceneMaster.model_validate(item) for item in result.items]
