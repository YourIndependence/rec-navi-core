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
    """Serve scene thumbnail or guide image without authentication (GET endpoint for <img src>)."""
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
    """Serve template thumbnail image without authentication (GET endpoint for <img src>)."""
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
