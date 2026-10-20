# Copyright (c) 2026 YourIndependence. All rights reserved.

"""Template URL and persistence boundaries."""

from unittest.mock import AsyncMock
from unittest.mock import call

import pytest

from recnavi.core.types.scenes_template import ScenesTemplate
from tests.mockups.mock_object_storage import MockObjectStorage


@pytest.mark.asyncio
async def test_template_refreshes_urls_and_preserves_storage_round_trip():
    template = ScenesTemplate(
        template_id="cafe",
        title="Cafe",
        scene_principals=["opening", "closing"],
        thumbnail_uri="templates/cafe.jpg",
    )
    original = template.to_storage_item()
    storage = MockObjectStorage(bucket_name="media")
    storage.generate_presigned_url = AsyncMock(
        side_effect=["https://signed/first", "https://signed/second"],
    )
    assert await template.attach_presigned_url(storage=storage) is template
    assert template.thumbnail_url == "https://signed/first"
    assert await template.attach_presigned_url(storage=storage) is template
    assert template.thumbnail_url == "https://signed/second"
    assert template.to_storage_item() == original
    restored = ScenesTemplate.model_validate(template.to_storage_item())
    assert restored.thumbnail_uri == "templates/cafe.jpg"
    assert restored.scene_principals == ["opening", "closing"]
    assert restored.thumbnail_url is None
    assert template.model_dump(by_alias=True) == {
        "templateId": "cafe",
        "title": "Cafe",
        "scenePrincipals": ["opening", "closing"],
        "thumbnailUrl": "https://signed/second",
    }
    storage.generate_presigned_url.assert_has_awaits(
        [call(object_key="templates/cafe.jpg", expiration=3600)] * 2,
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "fields",
    [{}, {"thumbnail_uri": ""}, {"thumbnail_uri": None}],
)
async def test_missing_image_clears_stale_url(fields):
    template = ScenesTemplate(
        template_id="cafe",
        title="Cafe",
        thumbnail_url="https://signed/stale",
        **fields,
    )
    storage = MockObjectStorage(bucket_name="media")
    storage.generate_presigned_url = AsyncMock()
    assert await template.attach_presigned_url(storage=storage) is template
    assert template.thumbnail_url is None
    assert template.to_storage_item()["thumbnailUri"] == template.thumbnail_uri
    storage.generate_presigned_url.assert_not_awaited()


def test_template_response_schema_excludes_storage_reference():
    properties = ScenesTemplate.model_json_schema(mode="serialization")[
        "properties"
    ]
    assert "thumbnailUri" not in properties
    assert "thumbnailUrl" in properties
