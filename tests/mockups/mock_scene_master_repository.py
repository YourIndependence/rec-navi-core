# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

import pytest

from recnavi.core.repositories.scene_master_repository import (
    BaseSceneMasterRepository,
)
from recnavi.core.types.scene_master import SceneMaster


class MockSceneMasterRepository(BaseSceneMasterRepository):
    """Scene masters held in memory"""

    def __init__(self, masters: list[SceneMaster] | None = None) -> None:
        self.masters = get_mock_scene_masters() if masters is None else masters

    async def list_all(self) -> list[SceneMaster]:
        return self.masters


@pytest.fixture
def mock_scene_master_repository():
    return MockSceneMasterRepository()


def get_mock_scene_masters() -> list[SceneMaster]:
    """Get the scene masters used across tests"""
    return [
        SceneMaster(
            scene_principal="shop_gaikan",
            title="Shop exterior",
            thumbnail_uri="masters/shop_gaikan/example.jpg",
            guide_uri="masters/shop_gaikan/guide.png",
            max_duration_seconds=5,
        ),
        SceneMaster(
            scene_principal="main_dish",
            title="Signature dish",
            thumbnail_uri="masters/main_dish/example.jpg",
            guide_uri="masters/main_dish/guide.png",
            max_duration_seconds=3,
        ),
    ]
