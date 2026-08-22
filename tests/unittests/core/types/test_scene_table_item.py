# Copyright (c) 2025 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.


"""SceneTableItem tests"""

import pytest
from pydantic import ValidationError

from recnavi.core.types.scene_table_item import SceneTableItem


ITEM = {
    "scenePrincipal": "shop_gaikan",
    "title": "Shop exterior",
    "thumbnailUri": "assets/scenes/shop_gaikan/example.jpg",
    "guideUri": "assets/scenes/shop_gaikan/guide.png",
    "maxDurationSeconds": 10,
}


def test_load_from_table_item():
    scene = SceneTableItem.model_validate(ITEM)

    assert scene.scene_principal == "shop_gaikan"
    assert scene.guide_uri == "assets/scenes/shop_gaikan/guide.png"
    assert scene.max_duration_seconds == 10


def test_dump_to_table_item():
    scene = SceneTableItem.model_validate(ITEM)

    assert scene.model_dump(by_alias=True, mode="json") == ITEM


def test_reject_missing_partition_key():
    item = {
        key: value for key, value in ITEM.items() if key != "scenePrincipal"
    }

    with pytest.raises(ValidationError):
        SceneTableItem.model_validate(item)
