# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Get template thumbnail image use case."""

from collections.abc import AsyncIterator

from recnavi.core.database.base_database import BaseDatabase
from recnavi.core.scene.scenes_template import get_template_thumbnail
from recnavi.infrastructure.s3.s3_client import download_object_stream


async def get_template_thumbnail_usecase(
    *,
    templates_db: BaseDatabase,
    template_id: str,
    bucket_name: str,
) -> tuple[AsyncIterator[bytes], str]:
    """Get template thumbnail image."""
    return await get_template_thumbnail(
        templates_db=templates_db,
        template_id=template_id,
        bucket_name=bucket_name,
        download_stream=lambda bn, ok: download_object_stream(
            bucket_name=bn,
            object_key=ok,
        ),
    )
