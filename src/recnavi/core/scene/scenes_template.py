# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Scenes template domain logic."""

from urllib.parse import urlsplit

from recnavi.config.variables import SCENE_IMAGES_BUCKET_NAME
from recnavi.core.database.base_database import BaseDatabase
from recnavi.core.storage.base_object_storage import BaseObjectStorage
from recnavi.core.types.scenes_template import ScenesTemplate
from recnavi.exceptions.exceptions import ClientNotFoundError
from recnavi.exceptions.exceptions import ClientUnprocessableEntityError


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
    item = await templates_db.get_item({"templateId": template_id})
    if item is None:
        return None
    return ScenesTemplate.model_validate(item)


async def get_template_thumbnail(
    *,
    templates_db: BaseDatabase,
    template_id: str,
    storage: BaseObjectStorage,
) -> tuple[bytes, str]:
    """Get template thumbnail image bytes."""
    template = await get_template_by_id(
        templates_db=templates_db,
        template_id=template_id,
    )

    if template is None:
        raise ClientNotFoundError(
            f"Template '{template_id}' not found.",
        )

    object_key = template.thumbnail_uri
    if not object_key:
        raise ClientNotFoundError(
            f"Template '{template_id}' has no thumbnail.",
        )
    if "://" in object_key:
        uri = urlsplit(object_key)
        if (
            uri.scheme != "s3"
            or uri.netloc != SCENE_IMAGES_BUCKET_NAME
            or uri.query
            or uri.fragment
        ):
            raise ClientUnprocessableEntityError("Invalid template image URI.")
        object_key = uri.path.removeprefix("/")
    content_type = _infer_content_type(object_key)
    content = await storage.download_object(object_key=object_key)
    return content, content_type


def _infer_content_type(object_key: str) -> str:
    """Infer MIME type from file extension."""
    lower_key = object_key.lower()

    if lower_key.endswith((".jpg", ".jpeg")):
        return "image/jpeg"
    if lower_key.endswith(".png"):
        return "image/png"

    raise ClientUnprocessableEntityError("Unsupported template image format.")
