# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Update template use case."""

from recnavi.core.database.base_database import BaseDatabase
from recnavi.core.scene.update_template import update_template
from recnavi.core.storage.base_object_storage import BaseObjectStorage
from recnavi.core.types.scenes_template import ScenesTemplate
from recnavi.core.types.user import User


async def update_template_usecase(
    *,
    templates_db: BaseDatabase,
    scenes_db: BaseDatabase,
    storage: BaseObjectStorage,
    user: User,
    template_id: str,
    title: str | None = None,
    scene_principals: list[str] | None = None,
    thumbnail_image: str | None = None,
) -> ScenesTemplate:
    """Update a template and attach its temporary thumbnail URL."""
    template = await update_template(
        templates_db=templates_db,
        scenes_db=scenes_db,
        storage=storage,
        user=user,
        template_id=template_id,
        title=title,
        scene_principals=scene_principals,
        thumbnail_image=thumbnail_image,
    )
    return await template.attach_presigned_url(storage=storage)
