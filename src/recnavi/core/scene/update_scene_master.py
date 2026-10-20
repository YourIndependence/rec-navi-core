# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Scene master updates and persistence."""

from recnavi.core.database.base_database import BaseDatabase
from recnavi.core.storage.base_object_storage import BaseObjectStorage
from recnavi.core.types.scene_master import SceneMaster
from recnavi.core.types.user import User
from recnavi.core.types.user import UserRole
from recnavi.exceptions.exceptions import ClientAuthorizationError
from recnavi.exceptions.exceptions import ClientValueError


async def update_scene_master(
    *,
    scenes_db: BaseDatabase,
    storage: BaseObjectStorage,
    scene_principal: str,
    title: str | None = None,
    max_duration_seconds: int | None = None,
    thumbnail_image: str | None,
    guide_image: str | None,
    user: User,
) -> SceneMaster:
    """Validate and update a master before publishing its durable references."""
    if not user.can_act_as(UserRole.ADMIN):
        raise ClientAuthorizationError("Only admins can update scene masters")

    item = await scenes_db.get_item({"scenePrincipal": scene_principal})

    if item:
        scene_master = SceneMaster.model_validate(item)
        if title is not None:
            scene_master.title = title
        if max_duration_seconds is not None:
            scene_master.max_duration_seconds = max_duration_seconds

    else:
        if thumbnail_image is None or guide_image is None:
            raise ClientValueError(
                "thumbnailImage and guideImage are required when creating a new scene",
            )
        if title is None:
            raise ClientValueError("title is required.")
        if max_duration_seconds is None:
            raise ClientValueError("max_duration_seconds is required.")

        scene_master = SceneMaster(
            scene_principal=scene_principal,
            title=title,
            max_duration_seconds=max_duration_seconds,
        )

    if thumbnail_image is not None or guide_image is not None:
        scene_master = await scene_master.update_images(
            storage=storage,
            thumbnail_image=thumbnail_image,
            guide_image=guide_image,
        )
    return await scene_master.save(scenes_db=scenes_db)
