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
from recnavi.core.scene.upsert_template import upsert_template
from recnavi.core.types.scenes_template import ScenesTemplate
from recnavi.exceptions.exceptions import ClientUnprocessableEntityError
from recnavi.exceptions.exceptions import ClientValueError
from recnavi.infrastructure.s3.s3_client import upload_base64


async def update_template_usecase(
    *,
    templates_db: BaseDatabase,
    scenes_db: BaseDatabase,
    template_id: str,
    title: str,
    scene_principals: list[str],
    thumbnail: str | None,
    bucket_name: str,
) -> list[ScenesTemplate]:
    """Create or update template with thumbnail upload.

    Args:
        templates_db: Database for templates.
        scenes_db: Database for scene masters.
        template_id: Identifier of the template.
        title: Name shown to the owner.
        scene_principals: Scene masters to lay out, in shooting order.
        thumbnail: Base64-encoded thumbnail image (required on create).
        bucket_name: S3 bucket name for scene images.

    Returns:
        List of all templates after update.

    Raises:
        ClientUnprocessableEntityError: Thumbnail missing on create.
        ClientValueError: Unknown scenePrincipals.

    """
    result = await scenes_db.scan()
    existing_principals = {item["scenePrincipal"] for item in result.items}
    missing = [p for p in scene_principals if p not in existing_principals]
    if missing:
        raise ClientValueError(f"Unknown scenePrincipals: {missing}")

    existing_template = await templates_db.get_item(
        {"templateId": template_id},
    )

    if not existing_template:
        if not thumbnail:
            raise ClientUnprocessableEntityError(
                "thumbnail is required when creating a new template",
            )

        thumbnail_uri = (
            f"s3://{bucket_name}/templates/{template_id}/thumbnail.jpg"
        )

        await upload_base64(
            bucket_name=bucket_name,
            object_key=f"templates/{template_id}/thumbnail.jpg",
            base64_data=thumbnail,
            content_type="image/jpeg",
        )
    else:
        existing = ScenesTemplate.model_validate(existing_template)
        thumbnail_uri = existing.thumbnail_uri

        if thumbnail:
            await upload_base64(
                bucket_name=bucket_name,
                object_key=f"templates/{template_id}/thumbnail.jpg",
                base64_data=thumbnail,
                content_type="image/jpeg",
            )
            thumbnail_uri = (
                f"s3://{bucket_name}/templates/{template_id}/thumbnail.jpg"
            )

    await upsert_template(
        templates_db=templates_db,
        template_id=template_id,
        title=title,
        scene_principals=scene_principals,
        thumbnail_uri=thumbnail_uri,
    )

    result = await templates_db.scan()
    all_templates = [
        ScenesTemplate.model_validate(item) for item in result.items
    ]

    return all_templates
