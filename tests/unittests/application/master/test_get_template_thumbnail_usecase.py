# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Tests for get_template_thumbnail_usecase."""

from unittest.mock import ANY
from unittest.mock import AsyncMock
from unittest.mock import patch

import pytest

from recnavi.application.master.get_template_thumbnail_usecase import (
    get_template_thumbnail_usecase,
)
from recnavi.exceptions.exceptions import ClientResourcesNotFoundError
from tests.mockups.mock_database import MockDatabase


@pytest.mark.asyncio
async def test_usecase_delegates_to_get_template_thumbnail():
    """Test usecase delegates to core get_template_thumbnail collaborator."""
    mock_db = AsyncMock()
    expected_stream = object()
    expected_content_type = "image/jpeg"
    expected_output = (expected_stream, expected_content_type)

    with patch(
        "recnavi.application.master.get_template_thumbnail_usecase.get_template_thumbnail",
        new=AsyncMock(return_value=expected_output),
    ) as mock_get:
        result = await get_template_thumbnail_usecase(
            templates_db=mock_db,
            template_id="cafe_standard",
            bucket_name="test-bucket",
        )

    mock_get.assert_awaited_once_with(
        templates_db=mock_db,
        template_id="cafe_standard",
        bucket_name="test-bucket",
        download_stream=ANY,
    )
    assert result is expected_output


@pytest.mark.asyncio
async def test_usecase_returns_stream_and_content_type_for_template():
    """Test usecase returns byte stream and correct content type."""
    mock_db = MockDatabase(
        initial_items=[
            {
                "templateId": "cafe_standard",
                "title": "Cafe Standard",
                "scenePrincipals": ["shop_gaikan"],
                "thumbnailUri": "templates/cafe_standard/thumbnail.jpg",
            },
        ],
    )

    stream, content_type = await get_template_thumbnail_usecase(
        templates_db=mock_db,
        template_id="cafe_standard",
        bucket_name="test-bucket",
    )

    # Stream will be AsyncIterator - just verify it's not None
    assert stream is not None
    assert content_type == "image/jpeg"


@pytest.mark.asyncio
async def test_usecase_raises_404_when_template_not_found():
    """Test usecase raises 404 when template doesn't exist."""
    mock_db = MockDatabase(initial_items=[])

    with pytest.raises(
        ClientResourcesNotFoundError,
        match="Template 'nonexistent' not found",
    ):
        await get_template_thumbnail_usecase(
            templates_db=mock_db,
            template_id="nonexistent",
            bucket_name="test-bucket",
        )


@pytest.mark.asyncio
async def test_usecase_infers_jpeg_from_jpg_extension():
    """Test usecase infers image/jpeg from .jpg extension."""
    mock_db = MockDatabase(
        initial_items=[
            {
                "templateId": "test_template",
                "title": "Test",
                "scenePrincipals": [],
                "thumbnailUri": "templates/test.jpg",
            },
        ],
    )

    _, content_type = await get_template_thumbnail_usecase(
        templates_db=mock_db,
        template_id="test_template",
        bucket_name="test-bucket",
    )

    assert content_type == "image/jpeg"


@pytest.mark.asyncio
async def test_usecase_infers_jpeg_from_jpeg_extension():
    """Test usecase infers image/jpeg from .jpeg extension."""
    mock_db = MockDatabase(
        initial_items=[
            {
                "templateId": "test_template",
                "title": "Test",
                "scenePrincipals": [],
                "thumbnailUri": "templates/test.jpeg",
            },
        ],
    )

    _, content_type = await get_template_thumbnail_usecase(
        templates_db=mock_db,
        template_id="test_template",
        bucket_name="test-bucket",
    )

    assert content_type == "image/jpeg"


@pytest.mark.asyncio
async def test_usecase_infers_png_from_png_extension():
    """Test usecase infers image/png from .png extension."""
    mock_db = MockDatabase(
        initial_items=[
            {
                "templateId": "test_template",
                "title": "Test",
                "scenePrincipals": [],
                "thumbnailUri": "templates/test.png",
            },
        ],
    )

    _, content_type = await get_template_thumbnail_usecase(
        templates_db=mock_db,
        template_id="test_template",
        bucket_name="test-bucket",
    )

    assert content_type == "image/png"


@pytest.mark.asyncio
async def test_usecase_defaults_to_jpeg_for_unknown_extension():
    """Test usecase defaults to image/jpeg for unknown extensions."""
    mock_db = MockDatabase(
        initial_items=[
            {
                "templateId": "test_template",
                "title": "Test",
                "scenePrincipals": [],
                "thumbnailUri": "templates/test.webp",
            },
        ],
    )

    _, content_type = await get_template_thumbnail_usecase(
        templates_db=mock_db,
        template_id="test_template",
        bucket_name="test-bucket",
    )

    assert content_type == "image/jpeg"
