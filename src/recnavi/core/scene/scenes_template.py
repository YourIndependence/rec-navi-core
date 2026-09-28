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
from recnavi.core.types.scenes_template import ScenesTemplate


async def get_templates(templates_db: BaseDatabase) -> list[ScenesTemplate]:
    """Retrieve all scenes templates from the database."""
<<<<<<< HEAD
    items = await templates_db.scan()
    return [ScenesTemplate.model_validate(item) for item in items]


async def get_template_by_id(
    *,
    templates_db: BaseDatabase,
    template_id: str,
) -> ScenesTemplate | None:
    """Get a single template by ID.

    Args:
        templates_db: Database instance for templates table.
        template_id: Template identifier (e.g., "tpl_cafe").

    Returns:
        ScenesTemplate if found, None otherwise.

    """
    items = await templates_db.scan()

    for item in items:
        if item.get("templateId") == template_id:
            return ScenesTemplate.model_validate(item)

    return None
=======
    result = await templates_db.scan()
    return [ScenesTemplate.model_validate(item) for item in result.items]
>>>>>>> origin/dev
