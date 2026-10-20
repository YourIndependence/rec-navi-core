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


@pytest.mark.asyncio
async def test_thumbnail_failure_restores_model_and_retains_previous_image():
    from recnavi.core.types.scenes_template import ScenesTemplate
    from tests.mockups.mock_object_storage import MockObjectStorage

    storage = MockObjectStorage(bucket_name="test-bucket")
    template = ScenesTemplate(
        template_id="rollback",
        title="Rollback",
        thumbnail_uri="old.jpg",
        thumbnail_url="https://signed/old",
    )
    await storage.upload_base64(object_key="old.jpg", base64_data="b2xk")
    before = storage.objects.copy()
    with pytest.raises(RuntimeError, match="save failed"):
        async with template.update_thumbnail(
            storage=storage,
            thumbnail_image="bmV3",
        ):
            assert template.thumbnail_uri != "old.jpg"
            assert template.thumbnail_url is None
            raise RuntimeError("save failed")
    assert template.thumbnail_uri == "old.jpg"
    assert template.thumbnail_url == "https://signed/old"
    assert storage.objects == before


@pytest.mark.asyncio
async def test_thumbnail_upload_failure_cleans_partial_upload():
    from unittest.mock import AsyncMock

    from recnavi.core.types.scenes_template import ScenesTemplate
    from tests.mockups.mock_object_storage import MockObjectStorage

    storage = MockObjectStorage(bucket_name="test-bucket")
    upload = storage.upload_base64

    async def fail_after_upload(**kwargs):
        await upload(**kwargs)
        raise RuntimeError("upload failed")

    storage.upload_base64 = AsyncMock(side_effect=fail_after_upload)
    template = ScenesTemplate(
        template_id="failed",
        title="Failed",
        thumbnail_uri="old.jpg",
    )
    with pytest.raises(RuntimeError, match="upload failed"):
        async with template.update_thumbnail(
            storage=storage,
            thumbnail_image="bmV3",
        ):
            pytest.fail("Failed upload must not publish the image")
    assert template.thumbnail_uri == "old.jpg"
    assert storage.objects == {}


@pytest.mark.asyncio
@pytest.mark.parametrize("image", ["", "!invalid!"])
async def test_invalid_thumbnail_never_uploads(image):
    from recnavi.core.types.scenes_template import ScenesTemplate
    from tests.mockups.mock_object_storage import MockObjectStorage

    storage = MockObjectStorage(bucket_name="test-bucket")
    template = ScenesTemplate(template_id="invalid", title="Invalid")
    with pytest.raises(ValueError):
        async with template.update_thumbnail(
            storage=storage,
            thumbnail_image=image,
        ):
            pytest.fail("Invalid image must not be published")
    assert storage.objects == {}


@pytest.mark.asyncio
async def test_thumbnail_replacement_deletes_legacy_uri_by_exact_key():
    from recnavi.config.variables import MEDIA_BUCKET_NAME
    from recnavi.core.types.scenes_template import ScenesTemplate
    from tests.mockups.mock_object_storage import MockObjectStorage

    storage = MockObjectStorage(bucket_name=MEDIA_BUCKET_NAME)
    await storage.upload_base64(
        object_key="templates/legacy/old.jpg",
        base64_data="b2xk",
    )
    await storage.upload_base64(
        object_key="templates/legacy/other.jpg",
        base64_data="b3RoZXI=",
    )
    template = ScenesTemplate(
        template_id="legacy",
        title="Legacy",
        thumbnail_uri=f"s3://{MEDIA_BUCKET_NAME}/templates/legacy/old.jpg",
    )
    async with template.update_thumbnail(
        storage=storage,
        thumbnail_image="bmV3",
    ):
        assert (
            MEDIA_BUCKET_NAME,
            "templates/legacy/old.jpg",
        ) in storage.objects
    assert (
        MEDIA_BUCKET_NAME,
        "templates/legacy/old.jpg",
    ) not in storage.objects
    assert (MEDIA_BUCKET_NAME, "templates/legacy/other.jpg") in storage.objects
    assert (MEDIA_BUCKET_NAME, template.thumbnail_uri) in storage.objects
