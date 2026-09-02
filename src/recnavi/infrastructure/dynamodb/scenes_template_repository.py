# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.


"""Scenes templates stored in DynamoDB."""

import asyncio

from recnavi.core.repositories.scenes_template_repository import (
    BaseScenesTemplateRepository,
)
from recnavi.core.types.scenes_template import ScenesTemplate
from recnavi.infrastructure.dynamodb.client import scan_all


class DynamoDbScenesTemplateRepository(BaseScenesTemplateRepository):
    """Scenes templates read from the scene templates table."""

    def __init__(self, *, table_name: str) -> None:
        self._table_name = table_name

    async def list_all(self) -> list[ScenesTemplate]:
        """Return every scenes template.

        As with the scene masters, this is a small table shared by every
        tenant with no key to query it by, so it is scanned in full.
        """
        items = await asyncio.to_thread(scan_all, self._table_name)
        return [ScenesTemplate.model_validate(item) for item in items]
