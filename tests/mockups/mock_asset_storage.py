# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

import pytest

from recnavi.core.repositories.asset_storage import BaseAssetStorage


class MockAssetStorage(BaseAssetStorage):
    """Assets held in memory"""

    def __init__(self, objects: dict[str, bytes] | None = None) -> None:
        self.objects = get_mock_assets() if objects is None else objects

    async def read(self, *, key: str) -> bytes | None:
        return self.objects.get(key)


@pytest.fixture
def mock_asset_storage():
    return MockAssetStorage()


def get_mock_assets() -> dict[str, bytes]:
    """Get the stored assets used across tests"""
    return {
        "assets/scenes/shop_gaikan/example.jpg": b"example-shop_gaikan",
        "assets/scenes/shop_gaikan/guide.png": b"guide-shop_gaikan",
        "assets/scenes/main_dish/example.jpg": b"example-main_dish",
        "assets/scenes/main_dish/guide.png": b"guide-main_dish",
        "assets/templates/tpl_cafe.jpg": b"tile-tpl_cafe",
        "assets/templates/tpl_hotel.jpg": b"tile-tpl_hotel",
    }
