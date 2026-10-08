# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Upsert template domain logic."""

from collections.abc import Awaitable
from collections.abc import Callable

from recnavi.core.database.base_database import BaseDatabase
from recnavi.core.types.scenes_template import ScenesTemplate
from recnavi.exceptions.exceptions import ClientUnprocessableEntityError
from recnavi.exceptions.exceptions import ClientValueError


async def upsert_template(
    *,
    templates_db: BaseDatabase,
    template_id: str,
    title: str,
    scene_principals: list[str],
    thumbnail_uri: str,
) -> ScenesTemplate:
    """Create or update scenes template."""
    template = ScenesTemplate(
        template_id=template_id,
        title=title,
        scene_principals=scene_principals,
        thumbnail_uri=thumbnail_uri,
    )

    await templates_db.put_item(template.model_dump(by_alias=True))

    return template


async def update_template(
    *,
    templates_db: BaseDatabase,
    scenes_db: BaseDatabase,
    template_id: str,
    title: str,
    scene_principals: list[str],
    thumbnail: str | None,
    bucket_name: str,
    upload_image: Callable[[str, str, str], Awaitable[None]],
) -> list[ScenesTemplate]:
    """Create or update template with thumbnail upload."""
    result = await scenes_db.scan()
    existing_principals = {item["scenePrincipal"] for item in result.items}
    missing = [p for p in scene_principals if p not in existing_principals]
    if missing:
        raise ClientValueError(f"Unknown scenePrincipals: {missing}")

    existing_template = await templates_db.get_item(
        {"templateId": template_id},
    )
    object_key = f"templates/{template_id}/thumbnail.jpg"
    uploaded_uri = f"s3://{bucket_name}/{object_key}"

    if not existing_template:
        if not thumbnail:
            raise ClientUnprocessableEntityError(
                "thumbnail is required when creating a new template",
            )
        await upload_image(bucket_name, object_key, thumbnail)
        thumbnail_uri = uploaded_uri
    else:
        thumbnail_uri = ScenesTemplate.model_validate(
            existing_template,
        ).thumbnail_uri
        if thumbnail:
            await upload_image(bucket_name, object_key, thumbnail)
            thumbnail_uri = uploaded_uri

    await upsert_template(
        templates_db=templates_db,
        template_id=template_id,
        title=title,
        scene_principals=scene_principals,
        thumbnail_uri=thumbnail_uri,
    )

    result = await templates_db.scan()
    return [ScenesTemplate.model_validate(item) for item in result.items]
