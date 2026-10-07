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
from fastapi import Depends
from fastapi import Query
from fastapi import Request
from fastapi.responses import StreamingResponse

from recnavi.apis.auth.auth import verify_user
from recnavi.apis.schemas.project_schemas import GetProjectsResponse
from recnavi.application.master import get_template_thumbnail_usecase
from recnavi.application.project.get_projects import get_projects_usecase
from recnavi.config.variables import PROJECTS_TABLE_NAME
from recnavi.config.variables import SCENE_IMAGES_BUCKET_NAME
from recnavi.config.variables import TEMPLATES_TABLE_NAME
from recnavi.core.types.user import User


pub_router = APIRouter(tags=["Public"])


@pub_router.get("/getProjects")
async def get_projects_endpoint(
    request: Request,
    user: User = Depends(verify_user),
    limit: int = Query(default=20, ge=1, le=100),
    cursor: str | None = Query(default=None),
) -> GetProjectsResponse:
    """List projects assigned to the authenticated user."""
    projects_db = request.app.state.database[PROJECTS_TABLE_NAME]
    projects, next_cursor = await get_projects_usecase(
        projects_db=projects_db,
        group_id=user.group_id,
        user_id=user.user_id,
        limit=limit,
        cursor=cursor,
    )

    return GetProjectsResponse(
        projects=projects,
        next_cursor=next_cursor,
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
