# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Public endpoints for scene reference images."""

from typing import Literal

from fastapi import APIRouter
from fastapi import Query
from fastapi import Request
from fastapi.responses import Response

from recnavi.application.scene.get_scene_thumbnail import (
    get_scene_thumbnail_usecase,
)
from recnavi.config.variables import SCENES_TABLE_NAME


pub_router = APIRouter(tags=["Public"])


@pub_router.get("/getSceneThumbnail", response_class=Response)
async def get_scene_thumbnail_endpoint(
    request: Request,
    scene_principal: str = Query(..., alias="scenePrincipal", min_length=1),
    kind: Literal["example", "guide"] = Query(...),
) -> Response:
    """Serve public scene example or guide images for image elements."""
    content, content_type = await get_scene_thumbnail_usecase(
        scenes_db=request.app.state.database[SCENES_TABLE_NAME],
        scene_principal=scene_principal,
        kind=kind,
        storage=request.app.state.scene_images_storage,
    )
    return Response(
        content=content,
        media_type=content_type,
        headers={"Cache-Control": "public, max-age=86400"},
    )
