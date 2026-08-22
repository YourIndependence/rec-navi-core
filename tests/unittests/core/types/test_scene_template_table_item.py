# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""SceneTemplateTableItem tests"""

import pytest
from pydantic import ValidationError

from recnavi.core.types.scene_template_table_item import SceneTemplateTableItem


ITEM = {
    "templateId": "tpl_cafe",
    "title": "Cafe",
    "scenePrincipals": ["shop_gaikan", "main_dish", "main_dish"],
    "thumbnailUri": "assets/templates/tpl_cafe.jpg",
}


def test_load_from_table_item():
    template = SceneTemplateTableItem.model_validate(ITEM)

    assert template.template_id == "tpl_cafe"
    assert template.scene_principals == [
        "shop_gaikan",
        "main_dish",
        "main_dish",
    ]


def test_dump_to_table_item():
    template = SceneTemplateTableItem.model_validate(ITEM)

    assert template.model_dump(by_alias=True, mode="json") == ITEM


def test_reject_missing_partition_key():
    item = {key: value for key, value in ITEM.items() if key != "templateId"}

    with pytest.raises(ValidationError):
        SceneTemplateTableItem.model_validate(item)
