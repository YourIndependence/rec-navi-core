# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Unit tests for the master API schemas."""

from recnavi.apis.schemas.master_schemas import GetSceneMastersResponse
from recnavi.apis.schemas.master_schemas import GetTemplatesResponse
from tests.mockups.mock_scene_master_repository import get_mock_scene_masters
from tests.mockups.mock_scenes_template_repository import (
    get_mock_scenes_templates,
)


def test_serializes_in_camel_case():
    """The wire format is camelCase, the Python one is snake_case."""
    response = GetSceneMastersResponse.from_scene_masters(
        get_mock_scene_masters(),
    )

    body = response.model_dump(by_alias=True)

    assert body == {
        "status": "ok",
        "message": None,
        "scenes": [
            {
                "scenePrincipal": "shop_gaikan",
                "title": "Shop exterior",
                "maxDurationSeconds": 5,
            },
            {
                "scenePrincipal": "main_dish",
                "title": "Signature dish",
                "maxDurationSeconds": 3,
            },
        ],
    }


def test_keeps_the_object_keys_on_the_server():
    """A client never learns where the images are stored."""
    response = GetSceneMastersResponse.from_scene_masters(
        get_mock_scene_masters(),
    )

    body = str(response.model_dump(by_alias=True))

    assert "thumbnailUri" not in body
    assert "guideUri" not in body
    assert "masters/" not in body


def test_accepts_an_empty_list():
    """An empty table produces an empty list, not an error."""
    response = GetSceneMastersResponse.from_scene_masters([])

    assert response.scenes == []


def test_templates_serialize_in_camel_case():
    """The wire format is camelCase, the Python one is snake_case."""
    response = GetTemplatesResponse.from_scenes_templates(
        get_mock_scenes_templates(),
    )

    body = response.model_dump(by_alias=True)

    assert body == {
        "status": "ok",
        "message": None,
        "templates": [
            {
                "templateId": "tpl_cafe",
                "title": "Cafe",
                "scenePrincipals": [
                    "shop_gaikan",
                    "main_dish",
                    "main_dish",
                ],
            },
            {
                "templateId": "tpl_hotel",
                "title": "Hotel",
                "scenePrincipals": ["shop_gaikan", "room"],
            },
        ],
    }


def test_templates_keep_the_object_keys_on_the_server():
    """A client never learns where the tile images are stored."""
    response = GetTemplatesResponse.from_scenes_templates(
        get_mock_scenes_templates(),
    )

    body = str(response.model_dump(by_alias=True))

    assert "thumbnailUri" not in body
    assert "templates/" not in body


def test_templates_accept_an_empty_list():
    """An empty table produces an empty list, not an error."""
    assert GetTemplatesResponse.from_scenes_templates([]).templates == []
