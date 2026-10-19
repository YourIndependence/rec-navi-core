# Copyright (c) 2026 YourIndependence. All rights reserved.

"""Template listing orchestration."""

from unittest.mock import AsyncMock
from unittest.mock import patch

import pytest

from recnavi.application.scene.get_templates import get_templates_usecase
from recnavi.core.types.scenes_template import ScenesTemplate
from tests.mockups.mock_database import MockDatabase
from tests.mockups.mock_object_storage import MockObjectStorage


@pytest.mark.asyncio
async def test_get_templates_attaches_urls_in_order():
    database = MockDatabase()
    storage = MockObjectStorage(bucket_name="media")
    storage.generate_presigned_url = AsyncMock(
        side_effect=["https://signed/first", "https://signed/second"],
    )
    templates = [
        ScenesTemplate(
            template_id="first",
            title="First",
            thumbnail_uri="first.jpg",
        ),
        ScenesTemplate(
            template_id="second",
            title="Second",
            thumbnail_uri="second.png",
        ),
    ]
    with patch(
        "recnavi.application.scene.get_templates.get_templates",
        new=AsyncMock(return_value=templates),
    ) as get_metadata:
        result = await get_templates_usecase(
            templates_db=database,
            storage=storage,
        )
    get_metadata.assert_awaited_once_with(templates_db=database)
    assert result == templates
    assert [template.template_id for template in result] == ["first", "second"]
    assert all(
        actual is original
        for actual, original in zip(result, templates, strict=True)
    )
    assert [template.thumbnail_url for template in result] == [
        "https://signed/first",
        "https://signed/second",
    ]


@pytest.mark.asyncio
async def test_get_templates_returns_empty_list():
    storage = MockObjectStorage(bucket_name="media")
    storage.generate_presigned_url = AsyncMock()
    assert (
        await get_templates_usecase(
            templates_db=MockDatabase(),
            storage=storage,
        )
        == []
    )
    storage.generate_presigned_url.assert_not_awaited()
