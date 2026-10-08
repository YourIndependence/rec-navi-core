# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Update scene use case."""

from recnavi.core.database.base_database import BaseDatabase
from recnavi.core.scene.upsert_scene_master import update_scene
from recnavi.core.types.scene_master import SceneMaster
from recnavi.infrastructure.s3.s3_client import upload_base64


async def update_scene_usecase(
    *,
    scenes_db: BaseDatabase,
    scene_principal: str,
    title: str,
    max_duration_seconds: int,
    example_image: str | None,
    guide_image: str | None,
    bucket_name: str,
) -> list[SceneMaster]:
    """Create or update scene master with image upload."""
    return await update_scene(
        scenes_db=scenes_db,
        scene_principal=scene_principal,
        title=title,
        max_duration_seconds=max_duration_seconds,
        example_image=example_image,
        guide_image=guide_image,
        bucket_name=bucket_name,
        upload_image=lambda bn, ok, data: upload_base64(
            bucket_name=bn,
            object_key=ok,
            base64_data=data,
            content_type="image/jpeg",
        ),
    )
