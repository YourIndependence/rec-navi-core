# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Update template use case."""

from recnavi.core.database.base_database import BaseDatabase
from recnavi.core.scene.upsert_template import update_template
from recnavi.core.types.scenes_template import ScenesTemplate
from recnavi.infrastructure.s3.s3_client import upload_base64


async def update_template_usecase(
    *,
    templates_db: BaseDatabase,
    scenes_db: BaseDatabase,
    template_id: str,
    title: str,
    scene_principals: list[str],
    thumbnail: str | None,
    bucket_name: str,
) -> list[ScenesTemplate]:
    """Create or update template with thumbnail upload."""
    return await update_template(
        templates_db=templates_db,
        scenes_db=scenes_db,
        template_id=template_id,
        title=title,
        scene_principals=scene_principals,
        thumbnail=thumbnail,
        bucket_name=bucket_name,
        upload_image=lambda bn, ok, data: upload_base64(
            bucket_name=bn,
            object_key=ok,
            base64_data=data,
            content_type="image/jpeg",
        ),
    )
