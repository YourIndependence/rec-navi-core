# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Upsert template domain logic."""

import uuid

from recnavi.core.database.base_database import BaseDatabase
from recnavi.core.storage.base_object_storage import BaseObjectStorage
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


async def _upload_thumbnail(
    storage: BaseObjectStorage,
    bucket_name: str,
    object_key: str,
    thumbnail: str,
) -> None:
    """Upload base64 thumbnail as JPEG."""
    await storage.upload_base64(
        bucket_name=bucket_name,
        object_key=object_key,
        base64_data=thumbnail,
        content_type="image/jpeg",
    )


async def update_template(
    *,
    templates_db: BaseDatabase,
    scenes_db: BaseDatabase,
    template_id: str | None,
    title: str,
    scene_principals: list[str],
    thumbnail: str | None,
    bucket_name: str,
    storage: BaseObjectStorage,
) -> list[ScenesTemplate]:
    """Create or update template with thumbnail upload.

    A null template_id means create: a new id is issued.
    """
    result = await scenes_db.scan()
    existing_principals = {item["scenePrincipal"] for item in result.items}
    missing = [p for p in scene_principals if p not in existing_principals]
    if missing:
        raise ClientValueError(f"Unknown scenePrincipals: {missing}")

    existing_template = None
    if template_id is None:
        template_id = uuid.uuid4().hex
    else:
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
        await _upload_thumbnail(storage, bucket_name, object_key, thumbnail)
        thumbnail_uri = uploaded_uri
    else:
        thumbnail_uri = ScenesTemplate.model_validate(
            existing_template,
        ).thumbnail_uri
        if thumbnail:
            await _upload_thumbnail(
                storage,
                bucket_name,
                object_key,
                thumbnail,
            )
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
