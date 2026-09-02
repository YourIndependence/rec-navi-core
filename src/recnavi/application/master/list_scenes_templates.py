# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.


"""List the scenes templates."""

from recnavi.core.repositories.scenes_template_repository import (
    BaseScenesTemplateRepository,
)
from recnavi.core.types.scenes_template import ScenesTemplate


async def list_scenes_templates(
    *,
    repository: BaseScenesTemplateRepository,
) -> list[ScenesTemplate]:
    """Return every scenes template."""
    return await repository.list_all()
