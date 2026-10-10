# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Get scene thumbnail or guide image use case."""

from collections.abc import AsyncIterator

from recnavi.core.database.base_database import BaseDatabase
from recnavi.core.scene.scene_master import get_scene_thumbnail
from recnavi.core.storage.base_object_storage import BaseObjectStorage


async def get_scene_thumbnail_usecase(
    *,
    scenes_db: BaseDatabase,
    scene_principal: str,
    kind: str,
    bucket_name: str,
    storage: BaseObjectStorage,
) -> tuple[AsyncIterator[bytes], str]:
    """Get scene thumbnail or guide image."""
    return await get_scene_thumbnail(
        scenes_db=scenes_db,
        scene_principal=scene_principal,
        kind=kind,
        bucket_name=bucket_name,
        storage=storage,
    )
