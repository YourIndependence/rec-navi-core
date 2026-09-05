# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.


"""Master router"""

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import Query
from fastapi import Response
from fastapi import status

from recnavi.apis.auth.auth import get_authenticated_user
from recnavi.apis.dependencies import get_asset_storage
from recnavi.apis.dependencies import get_scene_master_repository
from recnavi.apis.dependencies import get_scenes_template_repository
from recnavi.apis.schemas.master_schemas import GetSceneMastersResponse
from recnavi.apis.schemas.master_schemas import GetTemplatesResponse
from recnavi.application.master.get_scene_image import get_scene_image
from recnavi.application.master.get_template_image import get_template_image
from recnavi.application.master.list_scene_masters import list_scene_masters
from recnavi.application.master.list_scenes_templates import (
    list_scenes_templates,
)
from recnavi.config.variables import ASSET_CACHE_CONTROL
from recnavi.core.repositories.asset_storage import BaseAssetStorage
from recnavi.core.repositories.scene_master_repository import (
    BaseSceneMasterRepository,
)
from recnavi.core.repositories.scenes_template_repository import (
    BaseScenesTemplateRepository,
)
from recnavi.core.types.image_asset import ImageAsset
from recnavi.core.types.scene_master import SceneImageKind


master_router = APIRouter(tags=["Master"])


@master_router.get(
    "/getSceneMasters",
    response_model=GetSceneMastersResponse,
    dependencies=[Depends(get_authenticated_user)],
)
async def get_scene_masters(
    repository: BaseSceneMasterRepository = Depends(
        get_scene_master_repository,
    ),
) -> GetSceneMastersResponse:
    """Return every scene master."""
    masters = await list_scene_masters(repository=repository)
    return GetSceneMastersResponse.from_scene_masters(masters)


@master_router.get(
    "/getTemplates",
    response_model=GetTemplatesResponse,
    dependencies=[Depends(get_authenticated_user)],
)
async def get_templates(
    repository: BaseScenesTemplateRepository = Depends(
        get_scenes_template_repository,
    ),
) -> GetTemplatesResponse:
    """Return every scenes template."""
    templates = await list_scenes_templates(repository=repository)
    return GetTemplatesResponse.from_scenes_templates(templates)


@master_router.get(
    "/getSceneThumbnail",
    response_class=Response,
    responses={200: {"content": {"image/*": {}}}},
)
async def get_scene_thumbnail(
    scene_principal: str = Query(..., alias="scenePrincipal"),
    kind: SceneImageKind = Query(...),
    repository: BaseSceneMasterRepository = Depends(
        get_scene_master_repository,
    ),
    storage: BaseAssetStorage = Depends(get_asset_storage),
) -> Response:
    """Serve one image of a scene master.

    This route carries no token on purpose. An img tag cannot send an
    Authorization header, and these are shooting instructions shared by
    every tenant, not customer data.
    """
    image = await get_scene_image(
        scene_principal=scene_principal,
        kind=kind,
        repository=repository,
        storage=storage,
    )
    return _image_response(image, missing="No image is stored for that scene.")


@master_router.get(
    "/getTemplateThumbnail",
    response_class=Response,
    responses={200: {"content": {"image/*": {}}}},
)
async def get_template_thumbnail(
    template_id: str = Query(..., alias="templateId"),
    repository: BaseScenesTemplateRepository = Depends(
        get_scenes_template_repository,
    ),
    storage: BaseAssetStorage = Depends(get_asset_storage),
) -> Response:
    """Serve the tile image of a scenes template.

    Carries no token for the same reason as getSceneThumbnail.
    """
    image = await get_template_image(
        template_id=template_id,
        repository=repository,
        storage=storage,
    )
    return _image_response(
        image,
        missing="No image is stored for that template.",
    )


def _image_response(image: ImageAsset | None, *, missing: str) -> Response:
    """Serve an image, or say it is not there.

    A record naming an object that is no longer stored is an operational
    mistake, so it answers 404 rather than being reported as a fault.
    """
    if image is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=missing,
        )

    return Response(
        content=image.content,
        media_type=image.media_type,
        headers={"Cache-Control": ASSET_CACHE_CONTROL},
    )
