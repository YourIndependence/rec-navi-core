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
from recnavi.apis.schemas.project_schemas import ProjectSummaryView
from recnavi.application.project.get_my_projects_usecase import (
    get_my_projects_usecase,
)
from recnavi.config.variables import PROJECTS_TABLE_NAME
from recnavi.core.types.user import User


pub_router = APIRouter(tags=["Public"])


@pub_router.get("/getMyProjects")
async def get_my_projects_endpoint(
    request: Request,
    user: User = Depends(verify_user),
    limit: int = Query(default=20, ge=1, le=100),
    cursor: str | None = Query(default=None),
) -> GetProjectsResponse:
    """List projects assigned to the authenticated user."""
    projects_db = request.app.state.database[PROJECTS_TABLE_NAME]
    projects, next_cursor = await get_my_projects_usecase(
        projects_db=projects_db,
        group_id=user.group_id,
        user_id=user.user_id,
        limit=limit,
        cursor=cursor,
    )

    project_views = [
        ProjectSummaryView(
            project_id=p.project_id,
            project_name=p.project_name,
            description=p.description,
            owner_user_id=p.owner_user_id,
            created_at=p.created_at,
            status=p.status,
        )
        for p in projects
    ]

    return GetProjectsResponse(
        projects=project_views,
        next_cursor=next_cursor,
    )
