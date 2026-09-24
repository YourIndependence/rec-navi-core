# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Upsert scene master domain logic."""

from recnavi.core.database.base_database import BaseDatabase
from recnavi.core.types.scene_master import SceneMaster
from recnavi.exceptions.exceptions import ClientUnprocessableEntityError


async def upsert_scene_master(
    *,
    scenes_db: BaseDatabase,
    scene_principal: str,
    title: str,
    max_duration_seconds: int,
    thumbnail_uri: str,
    guide_uri: str,
) -> SceneMaster:
    """Create or update scene master.

    Args:
        scenes_db: Database for scene masters.
        scene_principal: Identifier of the scene master.
        title: Name shown to the staff.
        max_duration_seconds: How long the staff may record (1-10 seconds).
        thumbnail_uri: S3 location of the example photo.
        guide_uri: S3 location of the framing guide.

    Returns:
        Created or updated SceneMaster.

    Raises:
        ClientUnprocessableEntityError: maxDurationSeconds not in range 1-10.

    """
    if not (1 <= max_duration_seconds <= 10):
        raise ClientUnprocessableEntityError(
            "maxDurationSeconds must be between 1 and 10 seconds",
        )

    scene_master = SceneMaster(
        scene_principal=scene_principal,
        title=title,
        max_duration_seconds=max_duration_seconds,
        thumbnail_uri=thumbnail_uri,
        guide_uri=guide_uri,
    )

    await scenes_db.put_item(scene_master.model_dump(by_alias=True))

    return scene_master
