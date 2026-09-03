# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Unit tests for the get scene image use case."""

import pytest

from recnavi.application.master.get_scene_image import get_scene_image
from recnavi.core.types.scene_image import SceneImageKind
from tests.mockups.mock_asset_storage import MockAssetStorage
from tests.mockups.mock_scene_master_repository import (
    MockSceneMasterRepository,
)


async def _fetch(kind: SceneImageKind, principal: str = "shop_gaikan"):
    """Fetch one image through the use case."""
    return await get_scene_image(
        scene_principal=principal,
        kind=kind,
        repository=MockSceneMasterRepository(),
        storage=MockAssetStorage(),
    )


@pytest.mark.asyncio
async def test_serves_the_example_photo():
    """The example kind resolves to the photo to imitate."""
    image = await _fetch(SceneImageKind.EXAMPLE)

    assert image is not None
    assert image.content == b"example-shop_gaikan"
    assert image.media_type == "image/jpeg"


@pytest.mark.asyncio
async def test_serves_the_framing_guide():
    """The guide kind resolves to the overlay, a png."""
    image = await _fetch(SceneImageKind.GUIDE)

    assert image is not None
    assert image.content == b"guide-shop_gaikan"
    assert image.media_type == "image/png"


@pytest.mark.asyncio
async def test_answers_nothing_for_an_unknown_principal():
    """A principal with no master has no image."""
    image = await _fetch(SceneImageKind.EXAMPLE, principal="nowhere")

    assert image is None


@pytest.mark.asyncio
async def test_answers_nothing_when_the_object_is_gone():
    """A master may name an object that is no longer stored."""
    image = await get_scene_image(
        scene_principal="shop_gaikan",
        kind=SceneImageKind.EXAMPLE,
        repository=MockSceneMasterRepository(),
        storage=MockAssetStorage(objects={}),
    )

    assert image is None
