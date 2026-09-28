# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""List the scenes templates available to the CMS."""

from recnavi.core.database.base_database import BaseDatabase
from recnavi.core.scene.scenes_template import get_templates
from recnavi.core.types.scenes_template import ScenesTemplate


async def get_templates_usecase(
    *,
    templates_db: BaseDatabase,
) -> list[ScenesTemplate]:
    """List every scenes template."""
    return await get_templates(templates_db=templates_db)
