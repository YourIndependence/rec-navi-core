# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Upsert scene master domain logic."""

from collections.abc import Awaitable
from collections.abc import Callable

from recnavi.core.database.base_database import BaseDatabase
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
    scene_principal: str,
    title: str,
    max_duration_seconds: int,
    example_image: str | None,
    guide_image: str | None,
    bucket_name: str,
    upload_image: Callable[[str, str, str], Awaitable[None]],
) -> list[SceneMaster]:
    """Create or update scene master with image upload."""
    existing_scene = await scenes_db.get_item(
        {"scenePrincipal": scene_principal}
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

        await upload_image(
            bucket_name,
            f"scenes/{scene_principal}/example.jpg",
            example_image,
        )
        await upload_image(
            bucket_name,
            f"scenes/{scene_principal}/guide.jpg",
            guide_image,
        )
    else:
        existing_master = SceneMaster.model_validate(existing_scene)
        thumbnail_uri = existing_master.thumbnail_uri
        guide_uri = existing_master.guide_uri

        if example_image:
            await upload_image(
                bucket_name,
                f"scenes/{scene_principal}/example.jpg",
                example_image,
            )
            thumbnail_uri = (
                f"s3://{bucket_name}/scenes/{scene_principal}/example.jpg"
            )

        if guide_image:
            await upload_image(
                bucket_name,
                f"scenes/{scene_principal}/guide.jpg",
                guide_image,
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
