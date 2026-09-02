# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.


"""Wiring between the api layer and the concrete implementations."""

from recnavi.config.variables import DDB_SCENES_TABLE
from recnavi.core.repositories.scene_master_repository import (
    BaseSceneMasterRepository,
)
from recnavi.infrastructure.dynamodb.scene_master_repository import (
    DynamoDbSceneMasterRepository,
)


def get_scene_master_repository() -> BaseSceneMasterRepository:
    """Get where the scene masters are kept."""
    return DynamoDbSceneMasterRepository(table_name=DDB_SCENES_TABLE)
