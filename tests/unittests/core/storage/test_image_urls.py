# Copyright (c) 2026 YourIndependence. All rights reserved.

"""Validate master image locations before signing."""

from unittest.mock import AsyncMock

import pytest

from recnavi.config.variables import MEDIA_BUCKET_NAME
from recnavi.core.storage.image_urls import generate_image_url
from recnavi.exceptions.exceptions import ClientUnprocessableEntityError


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "uri",
    [
        "masters/thumbnail.jpg",
        f"s3://{MEDIA_BUCKET_NAME}/masters/thumbnail.jpg",
    ],
)
async def test_image_reference_is_signed_in_media_bucket(uri):
    storage = AsyncMock()
    storage.generate_presigned_url.return_value = "https://signed/image"
    assert (
        await generate_image_url(storage=storage, image_uri=uri)
        == "https://signed/image"
    )
    storage.generate_presigned_url.assert_awaited_once_with(
        object_key="masters/thumbnail.jpg",
        expiration=3600,
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "uri",
    [
        "s3://other/image.jpg",
        "https://example.org/image.jpg",
        f"s3://{MEDIA_BUCKET_NAME}/image.jpg?x=1",
        f"s3://{MEDIA_BUCKET_NAME}/image.jpg#fragment",
        "image.svg",
        f"s3://{MEDIA_BUCKET_NAME}/",
    ],
)
async def test_invalid_reference_is_rejected_without_signing(uri):
    storage = AsyncMock()
    with pytest.raises(ClientUnprocessableEntityError):
        await generate_image_url(storage=storage, image_uri=uri)
    storage.generate_presigned_url.assert_not_awaited()


@pytest.mark.asyncio
async def test_signing_failure_is_not_hidden():
    storage = AsyncMock()
    storage.generate_presigned_url.side_effect = RuntimeError("signing failed")
    with pytest.raises(RuntimeError, match="signing failed"):
        await generate_image_url(storage=storage, image_uri="image.jpg")
