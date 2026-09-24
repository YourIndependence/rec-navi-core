# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or reproduction of this software is strictly prohibited.
#
# For internal use only.
# developer team.

"""Tests for upsert_template."""

import pytest

from recnavi.core.scene.upsert_template import upsert_template
from recnavi.core.types.scenes_template import ScenesTemplate
from tests.mockups.mock_database import MockDatabase


@pytest.mark.asyncio
async def test_upsert_template_creates_new_template():
    """Test upsert creates new template when it doesn't exist."""
    templates_db = MockDatabase()

    result = await upsert_template(
        templates_db=templates_db,
        template_id="new_template",
        title="New Template",
        scene_principals=["cooking", "plating"],
        thumbnail_uri="s3://bucket/templates/new_template/thumbnail.jpg",
    )

    assert isinstance(result, ScenesTemplate)
    assert result.template_id == "new_template"
    assert result.title == "New Template"
    assert result.scene_principals == ["cooking", "plating"]
    assert (
        result.thumbnail_uri
        == "s3://bucket/templates/new_template/thumbnail.jpg"
    )

    stored_item = await templates_db.get_item({"templateId": "new_template"})
    assert stored_item is not None
    assert stored_item["title"] == "New Template"


@pytest.mark.asyncio
async def test_upsert_template_updates_existing_template():
    """Test upsert updates existing template."""
    templates_db = MockDatabase()
    await templates_db.put_item(
        {
            "templateId": "existing_template",
            "title": "Old Title",
            "scenePrincipals": ["cooking"],
            "thumbnailUri": "s3://bucket/old_thumbnail.jpg",
        },
    )

    result = await upsert_template(
        templates_db=templates_db,
        template_id="existing_template",
        title="Updated Title",
        scene_principals=["cooking", "plating"],
        thumbnail_uri="s3://bucket/new_thumbnail.jpg",
    )

    assert isinstance(result, ScenesTemplate)
    assert result.template_id == "existing_template"
    assert result.title == "Updated Title"
    assert result.scene_principals == ["cooking", "plating"]
    assert result.thumbnail_uri == "s3://bucket/new_thumbnail.jpg"

    stored_item = await templates_db.get_item(
        {"templateId": "existing_template"},
    )
    assert stored_item["title"] == "Updated Title"
    assert stored_item["scenePrincipals"] == ["cooking", "plating"]


@pytest.mark.asyncio
async def test_upsert_template_preserves_scene_principals_order_and_duplicates():
    """Test upsert preserves scenePrincipals order and duplicates."""
    templates_db = MockDatabase()

    result = await upsert_template(
        templates_db=templates_db,
        template_id="duplicate_template",
        title="Duplicate Test",
        scene_principals=["cooking", "cooking", "plating", "cooking"],
        thumbnail_uri="s3://bucket/thumbnail.jpg",
    )

    assert result.scene_principals == [
        "cooking",
        "cooking",
        "plating",
        "cooking",
    ]

    stored_item = await templates_db.get_item(
        {"templateId": "duplicate_template"},
    )
    assert stored_item["scenePrincipals"] == [
        "cooking",
        "cooking",
        "plating",
        "cooking",
    ]
