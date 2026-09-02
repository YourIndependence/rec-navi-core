# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.


"""List the scene masters."""

from recnavi.core.repositories.scene_master_repository import (
    BaseSceneMasterRepository,
)
from recnavi.core.types.scene_master import SceneMaster


async def list_scene_masters(
    *,
    repository: BaseSceneMasterRepository,
) -> list[SceneMaster]:
    """Return every scene master."""
    return await repository.list_all()
