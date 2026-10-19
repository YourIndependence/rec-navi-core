# Copyright (c) 2026 YourIndependence. All rights reserved.

"""Presigned image URLs for stored master assets."""

from urllib.parse import urlsplit

from recnavi.config.variables import MEDIA_BUCKET_NAME
from recnavi.core.storage.base_object_storage import BaseObjectStorage
from recnavi.exceptions.exceptions import ClientUnprocessableEntityError


MEDIA_URL_EXPIRATION_SECONDS = 3600


async def generate_image_url(
    *,
    storage: BaseObjectStorage,
    image_uri: str | None,
) -> str | None:
    """Sign a supported image reference in the configured media bucket."""
    if not image_uri:
        return None
    object_key = image_uri
    if "://" in image_uri:
        uri = urlsplit(image_uri)
        if (
            uri.scheme != "s3"
            or uri.netloc != MEDIA_BUCKET_NAME
            or uri.query
            or uri.fragment
        ):
            raise ClientUnprocessableEntityError("Invalid master image URI.")
        object_key = uri.path.removeprefix("/")
    if not object_key.lower().endswith((".jpg", ".jpeg", ".png")):
        raise ClientUnprocessableEntityError(
            "Unsupported master image format.",
        )
    return await storage.generate_presigned_url(
        object_key=object_key,
        expiration=MEDIA_URL_EXPIRATION_SECONDS,
    )
