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
from fastapi import BackgroundTasks
from fastapi import Depends
from fastapi import Query
from fastapi import Request

from recnavi.apis.auth.auth import verify_user
from recnavi.apis.schemas.project_schemas import GetProjectsResponse
from recnavi.apis.schemas.project_schemas import SubmitProjectRequest
from recnavi.apis.schemas.project_schemas import SubmitProjectResponse
from recnavi.application.project.get_projects import get_projects_usecase
from recnavi.application.project.notify_project_submitted_usecase import (
    notify_project_submitted_usecase,
)
from recnavi.application.project.submit_project_usecase import (
    submit_project_usecase,
)
from recnavi.config.variables import FRONTEND_BASE_URL
from recnavi.config.variables import MEDIA_BUCKET_NAME
from recnavi.config.variables import PROJECTS_TABLE_NAME
from recnavi.config.variables import USERS_TABLE_NAME
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


@pub_router.post("/submitProject")
async def submit_project_endpoint(
    request: Request,
    payload: SubmitProjectRequest,
    background_tasks: BackgroundTasks,
    user: User = Depends(verify_user),
) -> SubmitProjectResponse:
    """Submit project for owner review (staff only)."""
    projects_db = request.app.state.database[PROJECTS_TABLE_NAME]

    updated_project, missing_scene_ids = await submit_project_usecase(
        projects_db=projects_db,
        storage=request.app.state.object_storage,
        bucket_name=MEDIA_BUCKET_NAME,
        project_id=payload.project_id,
        user=user,
    )

    if not missing_scene_ids:
        background_tasks.add_task(
            notify_project_submitted_usecase,
            users_db=request.app.state.database[USERS_TABLE_NAME],
            notifier=request.app.state.notifier,
            project=updated_project,
            submitter=user,
            base_url=FRONTEND_BASE_URL,
        )

    return SubmitProjectResponse(
        project=updated_project,
        missing_scene_ids=missing_scene_ids,
    )
