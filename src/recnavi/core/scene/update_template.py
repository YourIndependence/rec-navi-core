# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Template updates and persistence."""

import asyncio

from recnavi.core.database.base_database import BaseDatabase
from recnavi.core.storage.base_object_storage import BaseObjectStorage
from recnavi.core.types.scenes_template import ScenesTemplate
from recnavi.core.types.user import User
from recnavi.core.types.user import UserRole
from recnavi.exceptions.exceptions import ClientAuthorizationError
from recnavi.exceptions.exceptions import ClientValueError


async def update_template(
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
    """Create or partially update the template identified by the client key."""
    if not user.can_act_as(UserRole.ADMIN):
        raise ClientAuthorizationError("Only admins can update templates")

    item = await templates_db.get_item({"templateId": template_id})
    if item:
        template = ScenesTemplate.model_validate(item)
        if title is not None:
            template.title = title
        if scene_principals is not None:
            template.scene_principals = scene_principals
    else:
        if (
            title is None
            or scene_principals is None
            or thumbnail_image is None
        ):
            raise ClientValueError(
                "title, scenePrincipals and thumbnailImage are required when creating a new template",
            )
        template = ScenesTemplate(
            template_id=template_id,
            title=title,
            scene_principals=scene_principals,
        )

    if scene_principals is not None:
        principals = list(dict.fromkeys(template.scene_principals))
        scenes = await asyncio.gather(
            *(
                scenes_db.get_item({"scenePrincipal": principal})
                for principal in principals
            ),
        )
        missing = [
            principal
            for principal, scene in zip(principals, scenes, strict=True)
            if scene is None
        ]
        if missing:
            raise ClientValueError(f"Unknown scenePrincipals: {missing}")

    if thumbnail_image is not None:
        async with template.update_thumbnail(
            storage=storage,
            thumbnail_image=thumbnail_image,
        ):
            return await template.save(templates_db=templates_db)
    return await template.save(templates_db=templates_db)
