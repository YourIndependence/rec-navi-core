# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or reproduction of this software is strictly prohibited.
#
# For internal use only.
# developer team.

"""Tests for upsert_template."""

import base64
import re

import pytest

from recnavi.core.scene.upsert_template import update_template
from recnavi.core.scene.upsert_template import upsert_template
from recnavi.core.types.scenes_template import ScenesTemplate
from recnavi.exceptions.exceptions import ClientUnprocessableEntityError
from recnavi.exceptions.exceptions import ClientValueError
from tests.mockups.mock_database import MockDatabase
from tests.mockups.mock_object_storage import MockObjectStorage


@pytest.mark.asyncio
async def test_upsert_template_creates_new_template():
    """Test upsert creates new template when it doesn't exist."""
    templates_db = MockDatabase(key_names=("templateId",))

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
    templates_db = MockDatabase(key_names=("templateId",))
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
    templates_db = MockDatabase(key_names=("templateId",))

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


THUMB = base64.b64encode(b"fake-thumbnail").decode()
THUMB_URI = "s3://test-bucket/templates/{}/thumbnail.jpg"


async def _scenes_db() -> MockDatabase:
    scenes_db = MockDatabase()
    await scenes_db.put_item({"scenePrincipal": "cooking", "title": "Cooking"})
    await scenes_db.put_item({"scenePrincipal": "plating", "title": "Plating"})
    return scenes_db


@pytest.mark.asyncio
async def test_update_template_creates_template_and_uploads_thumbnail():
    """Test new template uploads the thumbnail as JPEG."""
    templates_db = MockDatabase(key_names=("templateId",))
    storage = MockObjectStorage()

    templates = await update_template(
        templates_db=templates_db,
        scenes_db=await _scenes_db(),
        template_id="new_template",
        title="New Template",
        scene_principals=["cooking", "plating"],
        thumbnail=THUMB,
        bucket_name="test-bucket",
        storage=storage,
    )

    assert len(templates) == 1
    assert templates[0].template_id == "new_template"
    assert templates[0].title == "New Template"
    assert templates[0].scene_principals == ["cooking", "plating"]
    assert templates[0].thumbnail_uri == THUMB_URI.format("new_template")
    assert storage.objects == {
        ("test-bucket", "templates/new_template/thumbnail.jpg"): (
            b"fake-thumbnail",
            "image/jpeg",
        ),
    }


@pytest.mark.asyncio
async def test_update_template_keeps_thumbnail_when_not_provided():
    """Test existing template keeps its thumbnail without upload."""
    templates_db = MockDatabase(key_names=("templateId",))
    await templates_db.put_item(
        {
            "templateId": "existing_template",
            "title": "Old Title",
            "scenePrincipals": ["cooking"],
            "thumbnailUri": THUMB_URI.format("existing_template"),
        },
    )
    storage = MockObjectStorage()

    templates = await update_template(
        templates_db=templates_db,
        scenes_db=await _scenes_db(),
        template_id="existing_template",
        title="Updated Title",
        scene_principals=["cooking"],
        thumbnail=None,
        bucket_name="test-bucket",
        storage=storage,
    )

    assert templates[0].title == "Updated Title"
    assert templates[0].thumbnail_uri == THUMB_URI.format("existing_template")
    assert storage.objects == {}


@pytest.mark.asyncio
async def test_update_template_replaces_thumbnail_of_existing_template():
    """Test existing template uploads a new thumbnail when provided."""
    templates_db = MockDatabase(key_names=("templateId",))
    await templates_db.put_item(
        {
            "templateId": "tpl",
            "title": "Old",
            "scenePrincipals": ["cooking"],
            "thumbnailUri": "s3://other/old.jpg",
        },
    )
    storage = MockObjectStorage()

    templates = await update_template(
        templates_db=templates_db,
        scenes_db=await _scenes_db(),
        template_id="tpl",
        title="Old",
        scene_principals=["cooking"],
        thumbnail=THUMB,
        bucket_name="test-bucket",
        storage=storage,
    )

    assert templates[0].thumbnail_uri == THUMB_URI.format("tpl")
    assert storage.objects[("test-bucket", "templates/tpl/thumbnail.jpg")] == (
        b"fake-thumbnail",
        "image/jpeg",
    )


@pytest.mark.asyncio
async def test_update_template_raises_422_when_thumbnail_missing_on_create():
    """Test creating without thumbnail raises 422 and uploads nothing."""
    storage = MockObjectStorage()

    with pytest.raises(
        ClientUnprocessableEntityError,
        match="thumbnail is required when creating a new template",
    ):
        await update_template(
            templates_db=MockDatabase(key_names=("templateId",)),
            scenes_db=await _scenes_db(),
            template_id="new_template",
            title="New Template",
            scene_principals=["cooking"],
            thumbnail=None,
            bucket_name="test-bucket",
            storage=storage,
        )

    assert storage.objects == {}


@pytest.mark.asyncio
async def test_update_template_raises_400_when_scene_principal_not_found():
    """Test unknown scenePrincipal raises 400 and uploads nothing."""
    storage = MockObjectStorage()

    with pytest.raises(ClientValueError, match="Unknown scenePrincipals"):
        await update_template(
            templates_db=MockDatabase(key_names=("templateId",)),
            scenes_db=await _scenes_db(),
            template_id="new_template",
            title="New Template",
            scene_principals=["cooking", "nonexistent_scene"],
            thumbnail=THUMB,
            bucket_name="test-bucket",
            storage=storage,
        )

    assert storage.objects == {}


@pytest.mark.asyncio
async def test_update_template_allows_empty_scene_principals():
    """Test empty scenePrincipals array is allowed."""
    templates = await update_template(
        templates_db=MockDatabase(key_names=("templateId",)),
        scenes_db=MockDatabase(),
        template_id="empty_template",
        title="Empty Template",
        scene_principals=[],
        thumbnail=THUMB,
        bucket_name="test-bucket",
        storage=MockObjectStorage(),
    )

    assert len(templates) == 1
    assert templates[0].scene_principals == []


@pytest.mark.asyncio
async def test_update_template_preserves_duplicates_and_order():
    """Test scenePrincipals duplicates and order are preserved."""
    principals = ["cooking", "cooking", "plating", "cooking"]

    templates = await update_template(
        templates_db=MockDatabase(key_names=("templateId",)),
        scenes_db=await _scenes_db(),
        template_id="duplicate_template",
        title="Duplicate Template",
        scene_principals=principals,
        thumbnail=THUMB,
        bucket_name="test-bucket",
        storage=MockObjectStorage(),
    )

    assert templates[0].scene_principals == principals


@pytest.mark.asyncio
async def test_update_template_issues_new_id_when_template_id_is_null():
    """Test a null templateId creates a template with an issued id."""
    templates_db = MockDatabase(key_names=("templateId",))
    storage = MockObjectStorage()

    templates = await update_template(
        templates_db=templates_db,
        scenes_db=await _scenes_db(),
        template_id=None,
        title="New Template",
        scene_principals=["cooking"],
        thumbnail=THUMB,
        bucket_name="test-bucket",
        storage=storage,
    )

    assert len(templates) == 1
    issued_id = templates[0].template_id
    assert re.fullmatch(r"[0-9a-f]{32}", issued_id)
    assert templates[0].thumbnail_uri == THUMB_URI.format(issued_id)
    assert (
        "test-bucket",
        f"templates/{issued_id}/thumbnail.jpg",
    ) in storage.objects
    stored = await templates_db.get_item({"templateId": issued_id})
    assert stored["title"] == "New Template"


@pytest.mark.asyncio
async def test_update_template_raises_422_when_null_id_without_thumbnail():
    """Test creating via a null id still requires the thumbnail."""
    templates_db = MockDatabase(key_names=("templateId",))
    storage = MockObjectStorage()

    with pytest.raises(ClientUnprocessableEntityError):
        await update_template(
            templates_db=templates_db,
            scenes_db=await _scenes_db(),
            template_id=None,
            title="New Template",
            scene_principals=["cooking"],
            thumbnail=None,
            bucket_name="test-bucket",
            storage=storage,
        )

    assert storage.objects == {}
    assert (await templates_db.scan()).items == []
