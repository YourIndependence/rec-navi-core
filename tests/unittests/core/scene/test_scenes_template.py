# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Tests for scenes template core logic."""

from unittest.mock import AsyncMock

import pytest

from recnavi.core.scene.scenes_template import attach_template_urls
from recnavi.core.scene.scenes_template import get_templates
from recnavi.core.types.scenes_template import ScenesTemplate
from tests.mockups.mock_database import MockDatabase


@pytest.mark.asyncio
async def test_get_templates_returns_all_templates():
    """Test get_templates returns all templates from database."""
    mock_db = MockDatabase(
        initial_items=[
            {
                "templateId": "cafe_standard",
                "title": "Cafe Standard",
                "scenePrincipals": ["shop_gaikan", "main_dish", "staff_intro"],
                "thumbnailUri": "s3://bucket/cafe_standard.jpg",
            },
            {
                "templateId": "restaurant_deluxe",
                "title": "Restaurant Deluxe",
                "scenePrincipals": ["shop_gaikan", "interior", "main_dish"],
                "thumbnailUri": "s3://bucket/restaurant_deluxe.jpg",
            },
        ],
    )

    result = await get_templates(templates_db=mock_db)

    assert len(result) == 2
    assert result[0].template_id == "cafe_standard"
    assert result[0].title == "Cafe Standard"
    assert result[0].scene_principals == [
        "shop_gaikan",
        "main_dish",
        "staff_intro",
    ]
    assert result[1].template_id == "restaurant_deluxe"
    assert result[1].title == "Restaurant Deluxe"


@pytest.mark.asyncio
async def test_get_templates_returns_empty_list_when_no_templates():
    """Test get_templates returns empty list when database is empty."""
    mock_db = MockDatabase(initial_items=[])

    result = await get_templates(templates_db=mock_db)

    assert result == []


@pytest.mark.asyncio
async def test_get_templates_preserves_scene_principals_order():
    """Test get_templates preserves order of scene_principals array."""
    mock_db = MockDatabase(
        initial_items=[
            {
                "templateId": "ordered_template",
                "title": "Ordered Template",
                "scenePrincipals": ["z_scene", "a_scene", "m_scene"],
                "thumbnailUri": "s3://bucket/ordered.jpg",
            },
        ],
    )

    result = await get_templates(templates_db=mock_db)

    assert result[0].scene_principals == ["z_scene", "a_scene", "m_scene"]


@pytest.mark.asyncio
async def test_get_templates_preserves_duplicates_in_scene_principals():
    """Test get_templates preserves duplicate values in scene_principals."""
    mock_db = MockDatabase(
        initial_items=[
            {
                "templateId": "cafe_with_duplicates",
                "title": "Cafe with Multiple Dishes",
                "scenePrincipals": ["shop_gaikan", "main_dish", "main_dish"],
                "thumbnailUri": "s3://bucket/cafe_duplicates.jpg",
            },
        ],
    )

    result = await get_templates(templates_db=mock_db)

    assert result[0].scene_principals == [
        "shop_gaikan",
        "main_dish",
        "main_dish",
    ]
    assert len(result[0].scene_principals) == 3


@pytest.mark.asyncio
async def test_templates_return_presigned_images_without_storage_uri():
    database = MockDatabase(
        initial_items=[
            {
                "templateId": "cafe",
                "title": "Cafe",
                "scenePrincipals": ["cooking"],
                "thumbnailUri": "templates/cafe.jpg",
            },
        ],
    )
    storage = AsyncMock()
    storage.generate_presigned_url.return_value = "https://signed/template"
    result = await attach_template_urls(
        templates=await get_templates(templates_db=database),
        storage=storage,
    )
    assert result[0].model_dump(by_alias=True) == {
        "templateId": "cafe",
        "title": "Cafe",
        "scenePrincipals": ["cooking"],
        "thumbnailUrl": "https://signed/template",
    }
    storage.generate_presigned_url.assert_awaited_once_with(
        object_key="templates/cafe.jpg",
        expiration=3600,
    )
    storage.download_object.assert_not_awaited()


@pytest.mark.asyncio
async def test_template_url_attachment_preserves_model_and_source():
    template = ScenesTemplate(
        template_id="cafe",
        title="Cafe",
        thumbnail_uri="templates/cafe.jpg",
    )
    storage = AsyncMock()
    storage.generate_presigned_url.return_value = "https://signed/template"
    result = await attach_template_urls(templates=[template], storage=storage)
    assert isinstance(result[0], ScenesTemplate)
    assert result[0].thumbnail_uri == "templates/cafe.jpg"
    assert result[0].thumbnail_url == "https://signed/template"
    assert template.thumbnail_url is None
    assert "thumbnailUri" not in result[0].model_dump(by_alias=True)


@pytest.mark.asyncio
@pytest.mark.parametrize("value", ["", None])
async def test_templates_without_images_return_null(value):
    database = MockDatabase(
        initial_items=[
            {
                "templateId": "cafe",
                "title": "Cafe",
                "thumbnailUri": value,
            },
        ],
    )
    storage = AsyncMock()
    result = await attach_template_urls(
        templates=await get_templates(templates_db=database),
        storage=storage,
    )
    assert result[0].thumbnail_url is None
    storage.generate_presigned_url.assert_not_awaited()
