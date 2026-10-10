# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Public router for staff-facing endpoints."""

from typing import Literal

from fastapi import APIRouter
from fastapi import Depends
from fastapi import Query
from fastapi import Request
from fastapi.responses import StreamingResponse

from recnavi.apis.auth.auth import verify_user
from recnavi.apis.schemas.project_schemas import GetProjectsResponse
from recnavi.application.project.get_projects import get_projects_usecase
from recnavi.application.scene import get_scene_thumbnail_usecase
from recnavi.config.variables import PROJECTS_TABLE_NAME
from recnavi.config.variables import SCENE_IMAGES_BUCKET_NAME
from recnavi.config.variables import SCENES_TABLE_NAME
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


@pub_router.get("/getSceneThumbnail")
async def get_scene_thumbnail_endpoint(
    request: Request,
    scene_principal: str = Query(
        ...,
        alias="scenePrincipal",
        description="Scene principal identifier",
    ),
    kind: Literal["example", "guide"] = Query(
        ...,
        description="Image kind: 'example' or 'guide'",
    ),
) -> StreamingResponse:
    """Serve scene thumbnail or guide image without authentication (GET endpoint for <img src>)."""
    scenes_db = request.app.state.database[SCENES_TABLE_NAME]

    stream, content_type = await get_scene_thumbnail_usecase(
        scenes_db=scenes_db,
        scene_principal=scene_principal,
        kind=kind,
        bucket_name=SCENE_IMAGES_BUCKET_NAME,
        storage=request.app.state.object_storage,
    )

    return StreamingResponse(
        content=stream,
        media_type=content_type,
        headers={"Cache-Control": "public, max-age=86400"},
    )
