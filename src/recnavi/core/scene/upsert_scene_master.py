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


async def upsert_scene_master(
    *,
    scenes_db: BaseDatabase,
    scene_master: SceneMaster,
) -> SceneMaster:
    """Persist an already validated scene master."""
    await scenes_db.put_item(scene_master.to_storage_item())
    return scene_master


async def update_scene_master(
    *,
    scenes_db: BaseDatabase,
    scene_principal: str,
    title: str,
    max_duration_seconds: int,
    example_image: str | None,
    guide_image: str | None,
    bucket_name: str,
    storage: BaseObjectStorage,
    user: User,
) -> SceneMaster:
    """Validate and update a master before publishing its durable references."""
    if not user.can_act_as(UserRole.ADMIN):
        raise ClientAuthorizationError("Only admins can update scene masters")

    update = SceneMaster(
        scene_principal=scene_principal,
        title=title,
        max_duration_seconds=max_duration_seconds,
    )
    item = await scenes_db.get_item({"scenePrincipal": update.scene_principal})

    if item:
        scene_master = SceneMaster.model_validate(item)
    else:
        if example_image is None or guide_image is None:
            raise ClientValueError(
                "exampleImage and guideImage are required when creating a new scene",
            )
        scene_master = update

    scene_master.title = update.title
    scene_master.max_duration_seconds = update.max_duration_seconds
    async with scene_master.update_images(
        storage=storage,
        bucket_name=bucket_name,
        example_image=example_image,
        guide_image=guide_image,
    ):
        return await upsert_scene_master(
            scenes_db=scenes_db,
            scene_master=scene_master,
        )
