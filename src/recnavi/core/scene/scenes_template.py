# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Scenes template domain logic."""

from collections.abc import AsyncIterator

from recnavi.core.database.base_database import BaseDatabase
from recnavi.core.storage.base_object_storage import BaseObjectStorage
from recnavi.core.types.scenes_template import ScenesTemplate
from recnavi.exceptions.exceptions import ClientResourcesNotFoundError


async def get_templates(templates_db: BaseDatabase) -> list[ScenesTemplate]:
    """Retrieve all scenes templates from the database."""
    result = await templates_db.scan()
    return [ScenesTemplate.model_validate(item) for item in result.items]


async def get_template_by_id(
    *,
    templates_db: BaseDatabase,
    template_id: str,
) -> ScenesTemplate | None:
    """Get a single template by ID."""
    result = await templates_db.scan()

    for item in result.items:
        if item.get("templateId") == template_id:
            return ScenesTemplate.model_validate(item)

    return None


async def get_template_thumbnail(
    *,
    templates_db: BaseDatabase,
    template_id: str,
    bucket_name: str,
    storage: BaseObjectStorage,
) -> tuple[AsyncIterator[bytes], str]:
    """Get template thumbnail image stream."""
    template = await get_template_by_id(
        templates_db=templates_db,
        template_id=template_id,
    )

    if template is None:
        raise ClientResourcesNotFoundError(
            f"Template '{template_id}' not found.",
        )

    content_type = _infer_content_type(template.thumbnail_uri)

    stream = storage.download_object_stream(
        bucket_name=bucket_name,
        object_key=template.thumbnail_uri,
    )

    return stream, content_type


def _infer_content_type(object_key: str) -> str:
    """Infer MIME type from file extension."""
    lower_key = object_key.lower()

    if lower_key.endswith((".jpg", ".jpeg")):
        return "image/jpeg"
    if lower_key.endswith(".png"):
        return "image/png"

    return "image/jpeg"
