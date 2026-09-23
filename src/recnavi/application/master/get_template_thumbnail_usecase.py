# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Get template thumbnail image use case."""

from collections.abc import AsyncIterator

from recnavi.core.database.base_database import BaseDatabase
from recnavi.core.scene.scenes_template import get_template_by_id
from recnavi.exceptions.exceptions import ClientResourcesNotFoundError
from recnavi.infrastructure.s3.s3_client import download_object_stream


async def get_template_thumbnail_usecase(
    *,
    templates_db: BaseDatabase,
    template_id: str,
    bucket_name: str,
) -> tuple[AsyncIterator[bytes], str]:
    """Get template thumbnail image.

    Args:
        templates_db: Database instance for templates table.
        template_id: Template identifier (e.g., "tpl_cafe").
        bucket_name: S3 bucket name for scene images.

    Returns:
        Tuple of (byte_stream, content_type).

    Raises:
        ClientResourcesNotFoundError: Template not found.

    """
    # Get template from database
    template = await get_template_by_id(
        templates_db=templates_db,
        template_id=template_id,
    )

    if template is None:
        raise ClientResourcesNotFoundError(
            f"Template '{template_id}' not found.",
        )

    # Infer content type from file extension
    content_type = _infer_content_type(template.thumbnail_uri)

    # Download from S3
    stream = download_object_stream(
        bucket_name=bucket_name,
        object_key=template.thumbnail_uri,
    )

    return stream, content_type


def _infer_content_type(object_key: str) -> str:
    """Infer MIME type from file extension.

    Args:
        object_key: S3 object key (e.g., "templates/cafe/thumbnail.jpg").

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
