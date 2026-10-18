# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Staff router for staff-facing endpoints."""

from fastapi import APIRouter
from fastapi import Depends
from fastapi import Query
from fastapi import Request

from recnavi.apis.auth.auth import verify_user
from recnavi.apis.schemas.project_schemas import GetProjectRequest
from recnavi.apis.schemas.project_schemas import GetProjectResponse
from recnavi.apis.schemas.project_schemas import GetProjectsResponse
from recnavi.apis.schemas.scene_schemas import UpdateSceneRequest
from recnavi.apis.schemas.scene_schemas import UpdateSceneResponse
from recnavi.application.project.get_project import get_project_usecase
from recnavi.application.project.get_projects import get_projects_usecase
from recnavi.application.scene.update_scene import update_scene_usecase
from recnavi.config.variables import PROJECTS_TABLE_NAME
from recnavi.core.types.user import User


staff_router = APIRouter(tags=["Staff"])


@staff_router.get("/getProjects")
async def get_projects_endpoint(
    request: Request,
    user: User = Depends(verify_user),
    limit: int = Query(default=20, ge=1, le=100),
    cursor: str | None = Query(default=None),
) -> GetProjectsResponse:
    """List projects assigned to the authenticated staff user."""
    projects_db = request.app.state.database[PROJECTS_TABLE_NAME]
    projects, next_cursor = await get_projects_usecase(
        projects_db=projects_db,
        user_id=user.user_id,
        group_id=user.group_id,
        limit=limit,
        cursor=cursor,
    )

    return GetProjectsResponse(
        projects=projects,
        next_cursor=next_cursor,
    )


@staff_router.post("/getProject")
async def get_project_endpoint(
    request: Request,
    item: GetProjectRequest,
    user: User = Depends(verify_user),
) -> GetProjectResponse:
    """Get a project with all scenes for the authenticated staff user."""
    projects_db = request.app.state.database[PROJECTS_TABLE_NAME]
    project = await get_project_usecase(
        projects_db=projects_db,
        project_id=item.project_id,
        user=user,
    )
    return GetProjectResponse(project=project)


@staff_router.post("/updateScene")
async def update_scene_endpoint(
    request: Request,
    payload: UpdateSceneRequest,
    user: User = Depends(verify_user),
) -> UpdateSceneResponse:
    """Upload scene recording (staff only)."""
    projects_db = request.app.state.database[PROJECTS_TABLE_NAME]

    updated_project = await update_scene_usecase(
        projects_db=projects_db,
        storage=request.app.state.object_storage,
        project_id=payload.project_id,
        scene_id=payload.scene_id,
        video_base64=payload.video,
        thumbnail_base64=payload.thumbnail,
        user=user,
    )

    return UpdateSceneResponse(project=updated_project)
