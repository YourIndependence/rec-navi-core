# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Get scene thumbnail or guide image use case."""

from collections.abc import AsyncIterator

from recnavi.core.database.base_database import BaseDatabase
from recnavi.core.scene.scene_master import get_scene_master_by_principal
from recnavi.exceptions.exceptions import ClientResourcesNotFoundError
from recnavi.exceptions.exceptions import ClientUnprocessableEntityError
from recnavi.infrastructure.s3.s3_client import download_object_stream


async def get_scene_thumbnail_usecase(
    *,
    scenes_db: BaseDatabase,
    scene_principal: str,
    kind: str,
    bucket_name: str,
) -> tuple[AsyncIterator[bytes], str]:
    """Get scene thumbnail or guide image.

    Args:
        scenes_db: Database instance for scenes table.
        scene_principal: Scene principal identifier (e.g., "cooking").
        kind: Image type - "example" for thumbnail or "guide" for overlay.
        bucket_name: S3 bucket name for scene images.

    Returns:
        Tuple of (byte_stream, content_type).

    Raises:
        ClientResourcesNotFoundError: Scene principal not found.
        ClientUnprocessableEntityError: Invalid kind parameter.

    """
    # Validate kind parameter
    if kind not in ("example", "guide"):
        raise ClientUnprocessableEntityError(
            f"Invalid kind: {kind}. Must be 'example' or 'guide'.",
        )

    # Get scene master from database
    scene_master = await get_scene_master_by_principal(
        scenes_db=scenes_db,
        scene_principal=scene_principal,
    )

    if scene_master is None:
        raise ClientResourcesNotFoundError(
            f"Scene principal '{scene_principal}' not found.",
        )

    # Select URI based on kind
    if kind == "example":
        object_key = scene_master.thumbnail_uri
    else:  # kind == "guide"
        object_key = scene_master.guide_uri

    # Infer content type from file extension
    content_type = _infer_content_type(object_key)

    # Download from S3
    stream = download_object_stream(
        bucket_name=bucket_name,
        object_key=object_key,
    )

    return stream, content_type


def _infer_content_type(object_key: str) -> str:
    """Infer MIME type from file extension.

    Args:
        object_key: S3 object key (e.g., "scenes/cooking/example.jpg").

    Returns:
        MIME type string (e.g., "image/jpeg", "image/png").

    """
    lower_key = object_key.lower()

    if lower_key.endswith((".jpg", ".jpeg")):
        return "image/jpeg"
    if lower_key.endswith(".png"):
        return "image/png"

    # Default to JPEG if extension unknown
    return "image/jpeg"
