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

from recnavi.apis.auth.auth import verify_user
from recnavi.apis.schemas.project_schemas import GetProjectsResponse
from recnavi.apis.schemas.scene_schemas import UpdateSceneRecordRequest
from recnavi.apis.schemas.scene_schemas import UpdateSceneRecordResponse
from recnavi.application.project.get_projects import get_projects_usecase
from recnavi.application.scene.update_scene_record_usecase import (
    update_scene_record_usecase,
)
from recnavi.config.variables import PROJECTS_TABLE_NAME
from recnavi.config.variables import VIDEO_BUCKET_NAME
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


@pub_router.post("/updateSceneRecord")
async def update_scene_record_endpoint(
    request: Request,
    payload: UpdateSceneRecordRequest,
    user: User = Depends(verify_user),
) -> UpdateSceneRecordResponse:
    """Upload scene recording (staff only)."""
    projects_db = request.app.state.database[PROJECTS_TABLE_NAME]

    updated_project = await update_scene_record_usecase(
        projects_db=projects_db,
        storage=request.app.state.object_storage,
        project_id=payload.project_id,
        scene_id=payload.scene_id,
        video_base64=payload.video,
        thumbnail_base64=payload.thumbnail,
        user=user,
        video_bucket_name=VIDEO_BUCKET_NAME,
    )

    return UpdateSceneRecordResponse(project=updated_project)
