# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Public endpoints for template reference images."""

from fastapi import APIRouter
from fastapi import Query
from fastapi import Request
from fastapi.responses import Response

from recnavi.application.scene.get_template_thumbnail import (
    get_template_thumbnail_usecase,
)
from recnavi.config.variables import TEMPLATES_TABLE_NAME


pub_router = APIRouter(tags=["Public"])


@pub_router.get("/getTemplateThumbnail", response_class=Response)
async def get_template_thumbnail_endpoint(
    request: Request,
    template_id: str = Query(..., alias="templateId", min_length=1),
) -> Response:
    """Serve public template thumbnails for image elements."""
    content, content_type = await get_template_thumbnail_usecase(
        templates_db=request.app.state.database[TEMPLATES_TABLE_NAME],
        template_id=template_id,
        storage=request.app.state.scene_images_storage,
    )
    return Response(
        content=content,
        media_type=content_type,
        headers={"Cache-Control": "public, max-age=86400"},
    )
