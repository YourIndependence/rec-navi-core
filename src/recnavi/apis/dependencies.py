# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.


"""Wiring between the api layer and the concrete implementations."""

from recnavi.config.variables import DDB_SCENE_TEMPLATES_TABLE
from recnavi.config.variables import DDB_SCENES_TABLE
from recnavi.config.variables import MEDIA_BUCKET_NAME
from recnavi.core.repositories.asset_storage import BaseAssetStorage
from recnavi.core.repositories.scene_master_repository import (
    BaseSceneMasterRepository,
)
from recnavi.core.repositories.scenes_template_repository import (
    BaseScenesTemplateRepository,
)
from recnavi.infrastructure.dynamodb.scene_master_repository import (
    DynamoDbSceneMasterRepository,
)
from recnavi.infrastructure.dynamodb.scenes_template_repository import (
    DynamoDbScenesTemplateRepository,
)
from recnavi.infrastructure.s3.asset_storage import S3AssetStorage


def get_scene_master_repository() -> BaseSceneMasterRepository:
    """Get where the scene masters are kept."""
    return DynamoDbSceneMasterRepository(table_name=DDB_SCENES_TABLE)


def get_scenes_template_repository() -> BaseScenesTemplateRepository:
    """Get where the scenes templates are kept."""
    return DynamoDbScenesTemplateRepository(
        table_name=DDB_SCENE_TEMPLATES_TABLE,
    )


def get_asset_storage() -> BaseAssetStorage:
    """Get where the application assets are kept."""
    return S3AssetStorage(bucket_name=MEDIA_BUCKET_NAME)
