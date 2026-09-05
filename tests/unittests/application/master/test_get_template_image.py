# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Unit tests for the get template image use case."""

import pytest

from recnavi.application.master.get_template_image import get_template_image
from tests.mockups.mock_asset_storage import MockAssetStorage
from tests.mockups.mock_scenes_template_repository import (
    MockScenesTemplateRepository,
)


@pytest.mark.asyncio
async def test_serves_the_tile_image():
    """The template resolves to the image shown on its tile."""
    image = await get_template_image(
        template_id="tpl_cafe",
        repository=MockScenesTemplateRepository(),
        storage=MockAssetStorage(),
    )

    assert image is not None
    assert image.content == b"tile-tpl_cafe"
    assert image.media_type == "image/jpeg"


@pytest.mark.asyncio
async def test_answers_nothing_for_an_unknown_template():
    """A template that does not exist has no image."""
    image = await get_template_image(
        template_id="tpl_nowhere",
        repository=MockScenesTemplateRepository(),
        storage=MockAssetStorage(),
    )

    assert image is None


@pytest.mark.asyncio
async def test_answers_nothing_when_the_object_is_gone():
    """A template may name an object that is no longer stored."""
    image = await get_template_image(
        template_id="tpl_cafe",
        repository=MockScenesTemplateRepository(),
        storage=MockAssetStorage(objects={}),
    )

    assert image is None
