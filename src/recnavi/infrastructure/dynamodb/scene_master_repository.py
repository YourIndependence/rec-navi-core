# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.


"""Scene masters stored in DynamoDB."""

import asyncio

from recnavi.core.repositories.scene_master_repository import (
    BaseSceneMasterRepository,
)
from recnavi.core.types.scene_master import SceneMaster
from recnavi.infrastructure.dynamodb.client import get_item
from recnavi.infrastructure.dynamodb.client import scan_all


class DynamoDbSceneMasterRepository(BaseSceneMasterRepository):
    """Scene masters read from the scenes table."""

    def __init__(self, *, table_name: str) -> None:
        self._table_name = table_name

    async def list_all(self) -> list[SceneMaster]:
        """Return every scene master.

        The masters are a few dozen rows shared by every tenant and there
        is no key to query them by, so the whole table is scanned.
        """
        items = await asyncio.to_thread(scan_all, self._table_name)
        return [SceneMaster.model_validate(item) for item in items]

    async def get(self, *, scene_principal: str) -> SceneMaster | None:
        """Return one scene master, or nothing when there is none."""
        item = await asyncio.to_thread(
            get_item,
            self._table_name,
            {"scenePrincipal": scene_principal},
        )
        return None if item is None else SceneMaster.model_validate(item)
