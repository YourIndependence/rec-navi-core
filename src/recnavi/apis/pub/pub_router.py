# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Public router for staff-facing endpoints."""

from fastapi import APIRouter
from fastapi import Query
from fastapi import Request
from fastapi.responses import StreamingResponse

from recnavi.application.master import get_template_thumbnail_usecase
from recnavi.application.scene import get_scene_thumbnail_usecase
from recnavi.config.variables import SCENE_IMAGES_BUCKET_NAME
from recnavi.config.variables import SCENES_TABLE_NAME
from recnavi.config.variables import TEMPLATES_TABLE_NAME


pub_router = APIRouter(tags=["Public"])


@pub_router.get("/getSceneThumbnail")
async def get_scene_thumbnail_endpoint(
    request: Request,
    scene_principal: str = Query(
        ...,
        description="Scene principal identifier",
    ),
    kind: str = Query(..., description="Image kind: 'example' or 'guide'"),
) -> StreamingResponse:
    """Serve scene thumbnail or guide image without authentication.

    IMPORTANT: This endpoint intentionally violates 3 architecture rules:
    1. Uses GET with query params (not POST) - <img src> only supports GET
    2. Returns raw bytes (not BaseApiResponseModel) - returning actual image data
    3. No authentication - <img src> cannot send Authorization header

    Args:
        scene_principal: Scene identifier (e.g., "cooking")
        kind: Image type - "example" for thumbnail, "guide" for guide image

    Returns:
        StreamingResponse with image data and appropriate Content-Type

    Raises:
        404: Scene principal not found
        422: Invalid kind parameter (must be "example" or "guide")

    """
    scenes_db = request.app.state.database[SCENES_TABLE_NAME]

    stream, content_type = await get_scene_thumbnail_usecase(
        scenes_db=scenes_db,
        scene_principal=scene_principal,
        kind=kind,
        bucket_name=SCENE_IMAGES_BUCKET_NAME,
    )

    return StreamingResponse(
        content=stream,
        media_type=content_type,
        headers={"Cache-Control": "public, max-age=86400"},
    )


@pub_router.get("/getTemplateThumbnail")
async def get_template_thumbnail_endpoint(
    request: Request,
    template_id: str = Query(
        ...,
        description="Template identifier",
    ),
) -> StreamingResponse:
    """Serve template thumbnail image without authentication.

    IMPORTANT: This endpoint intentionally violates 3 architecture rules:
    1. Uses GET with query params (not POST) - <img src> only supports GET
    2. Returns raw bytes (not BaseApiResponseModel) - returning actual image data
    3. No authentication - <img src> cannot send Authorization header

    Args:
        template_id: Template identifier (e.g., "tpl_cafe")

    Returns:
        StreamingResponse with image data and appropriate Content-Type

    Raises:
        404: Template not found

    """
    templates_db = request.app.state.database[TEMPLATES_TABLE_NAME]

    stream, content_type = await get_template_thumbnail_usecase(
        templates_db=templates_db,
        template_id=template_id,
        bucket_name=SCENE_IMAGES_BUCKET_NAME,
    )

    return StreamingResponse(
        content=stream,
        media_type=content_type,
        headers={"Cache-Control": "public, max-age=86400"},
    )
