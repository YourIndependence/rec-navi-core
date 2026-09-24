# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Upsert template domain logic."""

from recnavi.core.database.base_database import BaseDatabase
from recnavi.core.types.scenes_template import ScenesTemplate


async def upsert_template(
    *,
    templates_db: BaseDatabase,
    template_id: str,
    title: str,
    scene_principals: list[str],
    thumbnail_uri: str,
) -> ScenesTemplate:
    """Create or update scenes template.

    Args:
        templates_db: Database for templates.
        template_id: Identifier of the template.
        title: Name shown to the owner.
        scene_principals: Scene masters to lay out, in shooting order.
        thumbnail_uri: S3 location of the thumbnail image.

    Returns:
        Created or updated ScenesTemplate.

    """
    template = ScenesTemplate(
        template_id=template_id,
        title=title,
        scene_principals=scene_principals,
        thumbnail_uri=thumbnail_uri,
    )

    await templates_db.put_item(template.model_dump(by_alias=True))

    return template
