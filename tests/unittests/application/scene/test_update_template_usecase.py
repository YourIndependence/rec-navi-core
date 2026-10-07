# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or reproduction of this software is strictly prohibited.
#
# For internal use only.
# developer team.

"""Tests for update_template_usecase."""

from unittest.mock import AsyncMock
from unittest.mock import patch

import pytest

from recnavi.application.scene.update_template_usecase import (
    update_template_usecase,
)
from recnavi.exceptions.exceptions import ClientUnprocessableEntityError
from recnavi.exceptions.exceptions import ClientValueError
from tests.mockups.mock_database import MockDatabase


@pytest.mark.asyncio
async def test_update_template_usecase_calls_upsert_template():
    """Test usecase calls core upsert_template to persist template."""
    templates_db = MockDatabase()
    scenes_db = MockDatabase()
    await scenes_db.put_item({"scenePrincipal": "cooking", "title": "Cooking"})
    await templates_db.put_item(
        {
            "templateId": "existing_template",
            "title": "Old Title",
            "scenePrincipals": ["cooking"],
            "thumbnailUri": "s3://test-bucket/templates/existing_template/thumbnail.jpg",
        },
    )

    with (
        patch(
            "recnavi.application.scene.update_template_usecase.upload_base64",
            new=AsyncMock(),
        ),
        patch(
            "recnavi.application.scene.update_template_usecase.upsert_template",
            new=AsyncMock(),
        ) as mock_upsert,
        patch.object(
            templates_db,
            "scan",
            new=AsyncMock(
                return_value=type(
                    "Result",
                    (),
                    {
                        "items": [
                            {
                                "templateId": "existing_template",
                                "title": "Updated Title",
                                "scenePrincipals": ["cooking"],
                                "thumbnailUri": "s3://test-bucket/templates/existing_template/thumbnail.jpg",
                            },
                        ],
                    },
                )(),
            ),
        ),
    ):
        result = await update_template_usecase(
            templates_db=templates_db,
            scenes_db=scenes_db,
            template_id="existing_template",
            title="Updated Title",
            scene_principals=["cooking"],
            thumbnail=None,
            bucket_name="test-bucket",
        )

    mock_upsert.assert_awaited_once_with(
        templates_db=templates_db,
        template_id="existing_template",
        title="Updated Title",
        scene_principals=["cooking"],
        thumbnail_uri="s3://test-bucket/templates/existing_template/thumbnail.jpg",
    )
    assert len(result) == 1
    assert result[0].template_id == "existing_template"


@pytest.mark.asyncio
async def test_update_template_usecase_creates_template_with_thumbnail():
    """Test usecase creates new template with uploaded thumbnail."""
    templates_db = MockDatabase()
    scenes_db = MockDatabase()
    await scenes_db.put_item(
        {"scenePrincipal": "cooking", "title": "Cooking"},
    )
    await scenes_db.put_item(
        {"scenePrincipal": "plating", "title": "Plating"},
    )

    mock_upload_base64 = AsyncMock()

    with patch(
        "recnavi.application.scene.update_template_usecase.upload_base64",
        mock_upload_base64,
    ):
        templates = await update_template_usecase(
            templates_db=templates_db,
            scenes_db=scenes_db,
            template_id="new_template",
            title="New Template",
            scene_principals=["cooking", "plating"],
            thumbnail="base64_thumbnail_data",
            bucket_name="test-bucket",
        )

    assert len(templates) == 1
    assert templates[0].template_id == "new_template"
    assert templates[0].title == "New Template"
    assert templates[0].scene_principals == ["cooking", "plating"]

    mock_upload_base64.assert_called_once_with(
        bucket_name="test-bucket",
        object_key="templates/new_template/thumbnail.jpg",
        base64_data="base64_thumbnail_data",
        content_type="image/jpeg",
    )


@pytest.mark.asyncio
async def test_update_template_usecase_updates_template_without_thumbnail():
    """Test usecase updates existing template without changing thumbnail."""
    templates_db = MockDatabase()
    scenes_db = MockDatabase()
    await scenes_db.put_item({"scenePrincipal": "cooking", "title": "Cooking"})
    await templates_db.put_item(
        {
            "templateId": "existing_template",
            "title": "Old Title",
            "scenePrincipals": ["cooking"],
            "thumbnailUri": "s3://test-bucket/templates/existing_template/thumbnail.jpg",
        },
    )

    mock_upload_base64 = AsyncMock()

    with patch(
        "recnavi.application.scene.update_template_usecase.upload_base64",
        mock_upload_base64,
    ):
        templates = await update_template_usecase(
            templates_db=templates_db,
            scenes_db=scenes_db,
            template_id="existing_template",
            title="Updated Title",
            scene_principals=["cooking"],
            thumbnail=None,
            bucket_name="test-bucket",
        )

    assert len(templates) == 1
    assert templates[0].template_id == "existing_template"
    assert templates[0].title == "Updated Title"
    assert (
        templates[0].thumbnail_uri
        == "s3://test-bucket/templates/existing_template/thumbnail.jpg"
    )

    mock_upload_base64.assert_not_called()


@pytest.mark.asyncio
async def test_update_template_usecase_raises_422_when_thumbnail_missing_on_create():
    """Test usecase raises 422 when creating without thumbnail."""
    templates_db = MockDatabase()
    scenes_db = MockDatabase()
    await scenes_db.put_item({"scenePrincipal": "cooking", "title": "Cooking"})

    with pytest.raises(
        ClientUnprocessableEntityError,
        match="thumbnail is required when creating a new template",
    ):
        await update_template_usecase(
            templates_db=templates_db,
            scenes_db=scenes_db,
            template_id="new_template",
            title="New Template",
            scene_principals=["cooking"],
            thumbnail=None,
            bucket_name="test-bucket",
        )


@pytest.mark.asyncio
async def test_update_template_usecase_raises_400_when_scene_principal_not_found():
    """Test usecase raises 400 when scenePrincipal doesn't exist."""
    templates_db = MockDatabase()
    scenes_db = MockDatabase()
    await scenes_db.put_item({"scenePrincipal": "cooking", "title": "Cooking"})

    with pytest.raises(
        ClientValueError,
        match="Unknown scenePrincipals",
    ):
        await update_template_usecase(
            templates_db=templates_db,
            scenes_db=scenes_db,
            template_id="new_template",
            title="New Template",
            scene_principals=["cooking", "nonexistent_scene"],
            thumbnail="base64_data",
            bucket_name="test-bucket",
        )


@pytest.mark.asyncio
async def test_update_template_usecase_allows_empty_scene_principals():
    """Test usecase allows empty scenePrincipals array."""
    templates_db = MockDatabase()
    scenes_db = MockDatabase()

    mock_upload_base64 = AsyncMock()

    with patch(
        "recnavi.application.scene.update_template_usecase.upload_base64",
        mock_upload_base64,
    ):
        templates = await update_template_usecase(
            templates_db=templates_db,
            scenes_db=scenes_db,
            template_id="empty_template",
            title="Empty Template",
            scene_principals=[],
            thumbnail="base64_data",
            bucket_name="test-bucket",
        )

    assert len(templates) == 1
    assert templates[0].template_id == "empty_template"
    assert templates[0].scene_principals == []


@pytest.mark.asyncio
async def test_update_template_usecase_preserves_duplicates_and_order():
    """Test usecase preserves scenePrincipals duplicates and order."""
    templates_db = MockDatabase()
    scenes_db = MockDatabase()
    await scenes_db.put_item({"scenePrincipal": "cooking", "title": "Cooking"})
    await scenes_db.put_item({"scenePrincipal": "plating", "title": "Plating"})

    mock_upload_base64 = AsyncMock()

    with patch(
        "recnavi.application.scene.update_template_usecase.upload_base64",
        mock_upload_base64,
    ):
        templates = await update_template_usecase(
            templates_db=templates_db,
            scenes_db=scenes_db,
            template_id="duplicate_template",
            title="Duplicate Template",
            scene_principals=["cooking", "cooking", "plating", "cooking"],
            thumbnail="base64_data",
            bucket_name="test-bucket",
        )

    assert len(templates) == 1
    assert templates[0].scene_principals == [
        "cooking",
        "cooking",
        "plating",
        "cooking",
    ]
