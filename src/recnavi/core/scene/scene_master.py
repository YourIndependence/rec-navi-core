# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Scene master domain logic."""

from urllib.parse import urlsplit

from recnavi.config.variables import SCENE_IMAGES_BUCKET_NAME
from recnavi.core.database.base_database import BaseDatabase
from recnavi.core.storage.base_object_storage import BaseObjectStorage
from recnavi.core.types.scene_master import SceneMaster
from recnavi.exceptions.exceptions import ClientNotFoundError
from recnavi.exceptions.exceptions import ClientUnprocessableEntityError


async def get_scene_masters(scenes_db: BaseDatabase) -> list[SceneMaster]:
    """Retrieve all scene masters from the database."""
    result = await scenes_db.scan()

    return [SceneMaster.model_validate(item) for item in result.items]


async def get_scene_master_by_principal(
    *,
    scenes_db: BaseDatabase,
    scene_principal: str,
) -> SceneMaster | None:
    """Get a single scene master by principal."""
    cursor = None
    while True:
        result = await scenes_db.scan(exclusive_start_key=cursor)
        for item in result.items:
            if item.get("scenePrincipal") == scene_principal:
                return SceneMaster.model_validate(item)
        cursor = result.last_evaluated_key
        if not cursor:
            return None


async def get_scene_thumbnail(
    *,
    scenes_db: BaseDatabase,
    scene_principal: str,
    kind: str,
    storage: BaseObjectStorage,
) -> tuple[bytes, str]:
    """Get scene thumbnail or guide image bytes."""
    if kind not in ("example", "guide"):
        raise ClientUnprocessableEntityError(
            f"Invalid kind: {kind}. Must be 'example' or 'guide'.",
        )

    scene_master = await get_scene_master_by_principal(
        scenes_db=scenes_db,
        scene_principal=scene_principal,
    )

    if scene_master is None:
        raise ClientNotFoundError(
            f"Scene principal '{scene_principal}' not found.",
        )

    if kind == "example":
        object_key = scene_master.thumbnail_uri
    else:
        object_key = scene_master.guide_uri

    if "://" in object_key:
        uri = urlsplit(object_key)
        if (
            uri.scheme != "s3"
            or uri.netloc != SCENE_IMAGES_BUCKET_NAME
            or uri.query
            or uri.fragment
        ):
            raise ClientUnprocessableEntityError("Invalid scene image URI.")
        object_key = uri.path.removeprefix("/")

    content_type = _infer_content_type(object_key)

    content = await storage.download_object(
        object_key=object_key,
    )

    return content, content_type


def _infer_content_type(object_key: str) -> str:
    """Infer MIME type from file extension."""
    lower_key = object_key.lower()

    if lower_key.endswith((".jpg", ".jpeg")):
        return "image/jpeg"
    if lower_key.endswith(".png"):
        return "image/png"

    raise ClientUnprocessableEntityError("Unsupported scene image format.")
