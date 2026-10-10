# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Upsert scene master domain logic."""

import uuid

from recnavi.core.database.base_database import BaseDatabase
from recnavi.core.storage.base_object_storage import BaseObjectStorage
from recnavi.core.types.scene_master import SceneMaster
from recnavi.exceptions.exceptions import ClientUnprocessableEntityError


async def upsert_scene_master(
    *,
    scenes_db: BaseDatabase,
    scene_principal: str,
    title: str,
    max_duration_seconds: int,
    thumbnail_uri: str,
    guide_uri: str,
) -> SceneMaster:
    """Create or update scene master."""
    if not (1 <= max_duration_seconds <= 10):
        raise ClientUnprocessableEntityError(
            "maxDurationSeconds must be between 1 and 10 seconds",
        )

    scene_master = SceneMaster(
        scene_principal=scene_principal,
        title=title,
        max_duration_seconds=max_duration_seconds,
        thumbnail_uri=thumbnail_uri,
        guide_uri=guide_uri,
    )

    await scenes_db.put_item(scene_master.model_dump(by_alias=True))

    return scene_master


async def update_scene(
    *,
    scenes_db: BaseDatabase,
    scene_principal: str | None,
    title: str,
    max_duration_seconds: int,
    example_image: str | None,
    guide_image: str | None,
    bucket_name: str,
    storage: BaseObjectStorage,
) -> list[SceneMaster]:
    """Create or update scene master with image upload.

    A null scene_principal means create: a new id is issued.
    """
    existing_scene = None
    if scene_principal is None:
        scene_principal = uuid.uuid4().hex
    else:
        existing_scene = await scenes_db.get_item(
            {"scenePrincipal": scene_principal},
        )

    if not existing_scene:
        if not example_image or not guide_image:
            raise ClientUnprocessableEntityError(
                "exampleImage and guideImage are required when creating a new scene",
            )

        thumbnail_uri = (
            f"s3://{bucket_name}/scenes/{scene_principal}/example.jpg"
        )
        guide_uri = f"s3://{bucket_name}/scenes/{scene_principal}/guide.jpg"

        await storage.upload_base64(
            bucket_name=bucket_name,
            object_key=f"scenes/{scene_principal}/example.jpg",
            base64_data=example_image,
            content_type="image/jpeg",
        )
        await storage.upload_base64(
            bucket_name=bucket_name,
            object_key=f"scenes/{scene_principal}/guide.jpg",
            base64_data=guide_image,
            content_type="image/jpeg",
        )
    else:
        existing_master = SceneMaster.model_validate(existing_scene)
        thumbnail_uri = existing_master.thumbnail_uri
        guide_uri = existing_master.guide_uri

        if example_image:
            await storage.upload_base64(
                bucket_name=bucket_name,
                object_key=f"scenes/{scene_principal}/example.jpg",
                base64_data=example_image,
                content_type="image/jpeg",
            )
            thumbnail_uri = (
                f"s3://{bucket_name}/scenes/{scene_principal}/example.jpg"
            )

        if guide_image:
            await storage.upload_base64(
                bucket_name=bucket_name,
                object_key=f"scenes/{scene_principal}/guide.jpg",
                base64_data=guide_image,
                content_type="image/jpeg",
            )
            guide_uri = (
                f"s3://{bucket_name}/scenes/{scene_principal}/guide.jpg"
            )

    await upsert_scene_master(
        scenes_db=scenes_db,
        scene_principal=scene_principal,
        title=title,
        max_duration_seconds=max_duration_seconds,
        thumbnail_uri=thumbnail_uri,
        guide_uri=guide_uri,
    )

    result = await scenes_db.scan()
    all_scenes = [SceneMaster.model_validate(item) for item in result.items]

    return all_scenes
