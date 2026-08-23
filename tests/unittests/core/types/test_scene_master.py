# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.


"""SceneMaster tests"""

import pytest
from pydantic import ValidationError

from recnavi.core.types.scene_master import SceneMaster


MASTER = {
    "scenePrincipal": "shop_gaikan",
    "title": "Shop exterior",
    "thumbnailUri": "assets/scenes/shop_gaikan/example.jpg",
    "guideUri": "assets/scenes/shop_gaikan/guide.png",
    "maxDurationSeconds": 10,
}


def test_load():
    master = SceneMaster.model_validate(MASTER)

    assert master.scene_principal == "shop_gaikan"
    assert master.guide_uri == "assets/scenes/shop_gaikan/guide.png"
    assert master.max_duration_seconds == 10


def test_dump_keeps_camel_case():
    master = SceneMaster.model_validate(MASTER)

    assert master.model_dump(by_alias=True, mode="json") == MASTER


def test_reject_missing_identifier():
    item = {
        key: value for key, value in MASTER.items() if key != "scenePrincipal"
    }

    with pytest.raises(ValidationError):
        SceneMaster.model_validate(item)
