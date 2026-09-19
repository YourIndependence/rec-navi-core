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
    items = await templates_db.scan()
    return [ScenesTemplate.model_validate(item) for item in items]
