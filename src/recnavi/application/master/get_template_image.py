# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.


"""Get the tile image of a scenes template."""

from recnavi.core.repositories.asset_storage import BaseAssetStorage
from recnavi.core.repositories.scenes_template_repository import (
    BaseScenesTemplateRepository,
)
from recnavi.core.types.image_asset import ImageAsset


async def get_template_image(
    *,
    template_id: str,
    repository: BaseScenesTemplateRepository,
    storage: BaseAssetStorage,
) -> ImageAsset | None:
    """Return the tile image, or nothing when there is none.

    The client asks by identifier, so the object key is resolved here and
    never travels.
    """
    template = await repository.get(template_id=template_id)
    if template is None:
        return None

    content = await storage.read(key=template.thumbnail_uri)
    if content is None:
        return None

    return ImageAsset.of(content=content, uri=template.thumbnail_uri)
