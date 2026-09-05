# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.


"""Get one image of a scene master."""

from recnavi.core.repositories.asset_storage import BaseAssetStorage
from recnavi.core.repositories.scene_master_repository import (
    BaseSceneMasterRepository,
)
from recnavi.core.types.image_asset import ImageAsset
from recnavi.core.types.scene_master import SceneImageKind


async def get_scene_image(
    *,
    scene_principal: str,
    kind: SceneImageKind,
    repository: BaseSceneMasterRepository,
    storage: BaseAssetStorage,
) -> ImageAsset | None:
    """Return one image of a scene master, or nothing when there is none.

    The client asks by principal, so the object key is resolved here and
    never travels.
    """
    master = await repository.get(scene_principal=scene_principal)
    if master is None:
        return None

    uri = (
        master.thumbnail_uri
        if kind is SceneImageKind.EXAMPLE
        else master.guide_uri
    )
    content = await storage.read(key=uri)
    if content is None:
        return None

    return ImageAsset.of(content=content, uri=uri)
