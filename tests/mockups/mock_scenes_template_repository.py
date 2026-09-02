# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

import pytest

from recnavi.core.repositories.scenes_template_repository import (
    BaseScenesTemplateRepository,
)
from recnavi.core.types.scenes_template import ScenesTemplate


class MockScenesTemplateRepository(BaseScenesTemplateRepository):
    """Scenes templates held in memory"""

    def __init__(self, templates: list[ScenesTemplate] | None = None) -> None:
        self.templates = (
            get_mock_scenes_templates() if templates is None else templates
        )

    async def list_all(self) -> list[ScenesTemplate]:
        return self.templates


@pytest.fixture
def mock_scenes_template_repository():
    return MockScenesTemplateRepository()


def get_mock_scenes_templates() -> list[ScenesTemplate]:
    """Get the scenes templates used across tests"""
    return [
        ScenesTemplate(
            template_id="tpl_cafe",
            title="Cafe",
            scene_principals=["shop_gaikan", "main_dish", "main_dish"],
            thumbnail_uri="templates/tpl_cafe/tile.jpg",
        ),
        ScenesTemplate(
            template_id="tpl_hotel",
            title="Hotel",
            scene_principals=["shop_gaikan", "room"],
            thumbnail_uri="templates/tpl_hotel/tile.jpg",
        ),
    ]
