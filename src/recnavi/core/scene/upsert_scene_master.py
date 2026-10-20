# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Scene master updates and persistence."""

from uuid import uuid4

from pydantic import ValidationError

from recnavi.core.database.base_database import BaseDatabase
from recnavi.core.storage.base_object_storage import BaseObjectStorage
from recnavi.core.types.scene_master import SceneMaster
from recnavi.core.types.scene_master_update import SceneMasterCreate
from recnavi.core.types.scene_master_update import SceneMasterUpdate
from recnavi.core.types.user import User
from recnavi.core.types.user import UserRole
from recnavi.exceptions.exceptions import ClientAuthorizationError
from recnavi.exceptions.exceptions import ClientUnprocessableEntityError


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

    update = SceneMasterUpdate(
        scene_principal=scene_principal,
        title=title,
        max_duration_seconds=max_duration_seconds,
        example_image=example_image,
        guide_image=guide_image,
    )
    item = await scenes_db.get_item({"scenePrincipal": update.scene_principal})
    if item:
        scene_master = SceneMaster.model_validate(item)
    else:
        try:
            SceneMasterCreate.model_validate(update.model_dump())
        except ValidationError as error:
            raise ClientUnprocessableEntityError(
                "exampleImage and guideImage are required when creating a new scene",
            ) from error
        scene_master = SceneMaster(
            scene_principal=update.scene_principal,
            title=update.title,
            max_duration_seconds=update.max_duration_seconds,
        )

    previous_images = {scene_master.thumbnail_uri, scene_master.guide_uri}
    scene_master.title = update.title
    scene_master.max_duration_seconds = update.max_duration_seconds
    image_prefix = f"scenes/{update.scene_principal}/{uuid4().hex}/"
    committed = False
    try:
        if update.example_image is not None:
            object_key = f"{image_prefix}example.jpg"
            await storage.upload_base64(
                object_key=object_key,
                base64_data=update.example_image,
                content_type="image/jpeg",
            )
            scene_master.thumbnail_uri = f"s3://{bucket_name}/{object_key}"
        if update.guide_image is not None:
            object_key = f"{image_prefix}guide.jpg"
            await storage.upload_base64(
                object_key=object_key,
                base64_data=update.guide_image,
                content_type="image/jpeg",
            )
            scene_master.guide_uri = f"s3://{bucket_name}/{object_key}"
        result = await upsert_scene_master(
            scenes_db=scenes_db,
            scene_master=scene_master,
        )
        committed = True
        current_images = {scene_master.thumbnail_uri, scene_master.guide_uri}
        owned_prefix = f"s3://{bucket_name}/scenes/{update.scene_principal}/"
        for image_uri in previous_images - current_images:
            if image_uri is not None and image_uri.startswith(owned_prefix):
                await storage.delete_object_by_key(
                    object_key=image_uri.removeprefix(f"s3://{bucket_name}/"),
                )
        return result
    finally:
        if not committed and (
            update.example_image is not None or update.guide_image is not None
        ):
            await storage.delete_objects_by_prefix(prefix=image_prefix)
