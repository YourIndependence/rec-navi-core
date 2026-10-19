# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Scenes template domain logic."""

from recnavi.core.database.base_database import BaseDatabase
from recnavi.core.storage.base_object_storage import BaseObjectStorage
from recnavi.core.storage.image_urls import generate_image_url
from recnavi.core.types.scenes_template import ScenesTemplate
from recnavi.core.types.scenes_template import ScenesTemplateView


async def get_templates(templates_db: BaseDatabase) -> list[ScenesTemplate]:
    """Retrieve all scenes templates from the database."""
    result = await templates_db.scan()
    return [ScenesTemplate.model_validate(item) for item in result.items]


async def attach_template_urls(
    *,
    templates: list[ScenesTemplate],
    storage: BaseObjectStorage,
) -> list[ScenesTemplateView]:
    """Replace template image references with temporary URLs."""
    return [
        ScenesTemplateView(
            template_id=template.template_id,
            title=template.title,
            scene_principals=template.scene_principals,
            thumbnail_url=await generate_image_url(
                storage=storage,
                image_uri=template.thumbnail_uri,
            ),
        )
        for template in templates
    ]
