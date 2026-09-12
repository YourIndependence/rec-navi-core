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
    """Retrieve all scenes templates from the database.

    This performs a full table scan. The templates table is small (dozens of rows,
    shared across all tenants), so a scan is acceptable here.

    The scene_principals array preserves order and duplicates, allowing templates
    like ["shop_gaikan", "main_dish", "main_dish"] for cafes with multiple dishes.

    Args:
        templates_db: Database instance for the templates table.

    Returns:
        List of all scenes templates. Empty list if no templates exist.

    """
    items = await templates_db.scan()

    return [ScenesTemplate.model_validate(item) for item in items]
