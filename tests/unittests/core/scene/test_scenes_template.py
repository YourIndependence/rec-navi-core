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

from recnavi.config.variables import SCENE_IMAGES_BUCKET_NAME
from recnavi.core.scene.scenes_template import get_template_by_id
from recnavi.core.scene.scenes_template import get_template_thumbnail
from recnavi.core.scene.scenes_template import get_templates
from recnavi.exceptions.exceptions import ClientNotFoundError
from recnavi.exceptions.exceptions import ClientUnprocessableEntityError
from tests.mockups.mock_database import MockDatabase
from tests.mockups.mock_object_storage import MockObjectStorage


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
async def test_get_template_by_id_returns_template_when_found():
    """Test get_template_by_id returns template when it exists."""
    mock_db = MockDatabase(
        initial_items=[
            {
                "templateId": "cafe_standard",
                "title": "Cafe Standard",
                "scenePrincipals": ["shop_gaikan", "main_dish"],
                "thumbnailUri": "s3://bucket/cafe_standard.jpg",
            },
            {
                "templateId": "restaurant_deluxe",
                "title": "Restaurant Deluxe",
                "scenePrincipals": ["interior", "main_dish"],
                "thumbnailUri": "s3://bucket/restaurant_deluxe.jpg",
            },
        ],
    )

    result = await get_template_by_id(
        templates_db=mock_db,
        template_id="cafe_standard",
    )

    assert result is not None
    assert result.template_id == "cafe_standard"
    assert result.title == "Cafe Standard"
    assert result.thumbnail_uri == "s3://bucket/cafe_standard.jpg"


@pytest.mark.asyncio
async def test_get_template_by_id_returns_none_when_not_found():
    """Test get_template_by_id returns None when template doesn't exist."""
    mock_db = MockDatabase(
        initial_items=[
            {
                "templateId": "cafe_standard",
                "title": "Cafe Standard",
                "scenePrincipals": ["shop_gaikan"],
                "thumbnailUri": "s3://bucket/cafe_standard.jpg",
            },
        ],
    )

    result = await get_template_by_id(
        templates_db=mock_db,
        template_id="nonexistent_template",
    )

    assert result is None


@pytest.mark.asyncio
async def test_get_template_by_id_returns_correct_template_from_multiple():
    """Test get_template_by_id returns correct template among multiple."""
    mock_db = MockDatabase(
        initial_items=[
            {
                "templateId": "template_a",
                "title": "Template A",
                "scenePrincipals": ["scene_a"],
                "thumbnailUri": "s3://bucket/a.jpg",
            },
            {
                "templateId": "template_b",
                "title": "Template B",
                "scenePrincipals": ["scene_b"],
                "thumbnailUri": "s3://bucket/b.jpg",
            },
            {
                "templateId": "template_c",
                "title": "Template C",
                "scenePrincipals": ["scene_c"],
                "thumbnailUri": "s3://bucket/c.jpg",
            },
        ],
    )

    result = await get_template_by_id(
        templates_db=mock_db,
        template_id="template_b",
    )

    assert result is not None
    assert result.template_id == "template_b"
    assert result.title == "Template B"


@pytest.mark.asyncio
async def test_template_lookup_uses_primary_key():
    database = AsyncMock()
    database.get_item.return_value = None
    assert (
        await get_template_by_id(templates_db=database, template_id="missing")
        is None
    )
    database.get_item.assert_awaited_once_with({"templateId": "missing"})
    database.scan.assert_not_awaited()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("key", "mime"),
    [
        ("thumb.jpg", "image/jpeg"),
        ("thumb.JPEG", "image/jpeg"),
        ("thumb.png", "image/png"),
        (f"s3://{SCENE_IMAGES_BUCKET_NAME}/thumb.png", "image/png"),
    ],
)
async def test_template_thumbnail_downloads_bytes(key, mime):
    database = MockDatabase(
        initial_items=[
            {"templateId": "cafe", "title": "Cafe", "thumbnailUri": key},
        ],
    )
    storage = MockObjectStorage(bucket_name=SCENE_IMAGES_BUCKET_NAME)
    storage.objects[(SCENE_IMAGES_BUCKET_NAME, key.rsplit("/", 1)[-1])] = (
        b"image",
        mime,
    )
    assert await get_template_thumbnail(
        templates_db=database,
        template_id="cafe",
        storage=storage,
    ) == (b"image", mime)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "key",
    [
        "s3://other-bucket/thumb.jpg",
        "https://example.org/thumb.jpg",
        "thumb.svg",
    ],
)
async def test_template_thumbnail_rejects_invalid_image_location(key):
    database = MockDatabase(
        initial_items=[
            {"templateId": "cafe", "title": "Cafe", "thumbnailUri": key},
        ],
    )
    with pytest.raises(ClientUnprocessableEntityError):
        await get_template_thumbnail(
            templates_db=database,
            template_id="cafe",
            storage=MockObjectStorage(bucket_name="images"),
        )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "items",
    [[], [{"templateId": "cafe", "title": "Cafe", "thumbnailUri": ""}]],
)
async def test_template_thumbnail_not_found(items):
    with pytest.raises(ClientNotFoundError):
        await get_template_thumbnail(
            templates_db=MockDatabase(initial_items=items),
            template_id="cafe",
            storage=MockObjectStorage(bucket_name="images"),
        )
