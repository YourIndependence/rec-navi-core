# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.


"""SceneTemplate tests"""

import pytest
from pydantic import ValidationError

from recnavi.core.types.scene_template import SceneTemplate


TEMPLATE = {
    "templateId": "tpl_cafe",
    "title": "Cafe",
    "scenePrincipals": ["shop_gaikan", "main_dish", "main_dish"],
    "thumbnailUri": "assets/templates/tpl_cafe.jpg",
}


def test_load():
    template = SceneTemplate.model_validate(TEMPLATE)

    assert template.template_id == "tpl_cafe"
    assert template.scene_principals == [
        "shop_gaikan",
        "main_dish",
        "main_dish",
    ]


def test_dump_keeps_camel_case():
    template = SceneTemplate.model_validate(TEMPLATE)

    assert template.model_dump(by_alias=True, mode="json") == TEMPLATE


def test_reject_missing_identifier():
    item = {
        key: value for key, value in TEMPLATE.items() if key != "templateId"
    }

    with pytest.raises(ValidationError):
        SceneTemplate.model_validate(item)
