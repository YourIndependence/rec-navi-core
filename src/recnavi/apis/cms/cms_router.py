# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""CMS router for content management endpoints."""

from fastapi import APIRouter
from fastapi import Depends
from fastapi import Query
from fastapi import Request

from recnavi.apis.auth.auth import verify_user
from recnavi.apis.schemas.project_schemas import CreateProjectRequest
from recnavi.apis.schemas.project_schemas import CreateProjectResponse
from recnavi.apis.schemas.project_schemas import DownloadProjectRequest
from recnavi.apis.schemas.project_schemas import DownloadProjectResponse
from recnavi.apis.schemas.project_schemas import GetProjectRequest
from recnavi.apis.schemas.project_schemas import GetProjectResponse
from recnavi.apis.schemas.project_schemas import GetProjectsResponse
from recnavi.apis.schemas.scene_schemas import GetSceneMastersResponse
from recnavi.apis.schemas.scene_schemas import SceneMasterView
from recnavi.apis.schemas.template_schemas import GetTemplatesResponse
from recnavi.application.project import download_project_usecase
from recnavi.application.project.create_project import create_project_usecase
from recnavi.application.project.get_project import get_project_usecase
from recnavi.application.project.get_projects import get_projects_usecase
from recnavi.application.scene.get_scene_masters import (
    get_scene_masters_usecase,
)
from recnavi.application.scene.get_templates import get_templates_usecase
from recnavi.config.variables import MEDIA_BUCKET_NAME
from recnavi.config.variables import PROJECTS_TABLE_NAME
from recnavi.config.variables import SCENES_TABLE_NAME
from recnavi.config.variables import TEMPLATES_TABLE_NAME
from recnavi.core.types.project import Project
from recnavi.core.types.user import User
from recnavi.exceptions.exceptions import ClientResourcesNotFoundError


cms_router = APIRouter(tags=["CMS"])


@cms_router.get(
    "/getSceneMasters",
    response_model=GetSceneMastersResponse,
)
async def get_scene_masters_endpoint(
    request: Request,
    _user: User = Depends(verify_user),
) -> GetSceneMastersResponse:
    """List all scene masters."""
    scenes_db = request.app.state.database[SCENES_TABLE_NAME]
    scene_masters = await get_scene_masters_usecase(scenes_db=scenes_db)

    scene_views = [
        SceneMasterView(
            scene_principal=sm.scene_principal,
            title=sm.title,
            max_duration_seconds=sm.max_duration_seconds,
        )
        for sm in scene_masters
    ]

    return GetSceneMastersResponse(scenes=scene_views)


@cms_router.get(
    "/getTemplates",
    response_model_exclude={"templates": {"__all__": {"thumbnail_uri"}}},
)
async def get_templates_endpoint(
    request: Request,
    _user: User = Depends(verify_user),
) -> GetTemplatesResponse:
    """List all scenes templates."""
    templates_db = request.app.state.database[TEMPLATES_TABLE_NAME]
    templates = await get_templates_usecase(templates_db=templates_db)
    return GetTemplatesResponse(templates=templates)


@cms_router.get("/getProjects")
async def get_projects_endpoint(
    request: Request,
    user: User = Depends(verify_user),
    limit: int = Query(default=20, ge=1, le=100),
    cursor: str | None = Query(default=None),
) -> GetProjectsResponse:
    """List projects for the authenticated user's group."""
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


@cms_router.post("/getProject")
async def get_project_endpoint(
    request: Request,
    item: GetProjectRequest,
    user: User = Depends(verify_user),
) -> GetProjectResponse:
    """Get a project with all scenes."""
    projects_db = request.app.state.database[PROJECTS_TABLE_NAME]

    project = await get_project_usecase(
        projects_db=projects_db,
        project_id=item.project_id,
        user=user,
    )

    return GetProjectResponse(project=project)


@cms_router.post("/createProject")
async def create_project_endpoint(
    request: Request,
    item: CreateProjectRequest,
    user: User = Depends(verify_user),
) -> CreateProjectResponse:
    """Create a new project."""
    projects_db = request.app.state.database[PROJECTS_TABLE_NAME]

    project = await create_project_usecase(
        projects_db=projects_db,
        project_name=item.project_name,
        description=item.description,
        scene_principals=item.scene_principals,
        assigned_user_ids=item.assigned_user_ids,
        owner=user,
    )

    return CreateProjectResponse(project=project)


@cms_router.post(
    "/downloadProject",
    response_model=DownloadProjectResponse,
)
async def download_project_endpoint(
    request: Request,
    item: DownloadProjectRequest,
    user: User = Depends(verify_user),
) -> DownloadProjectResponse:
    """Download approved project as zip archive."""
    projects_db = request.app.state.database[PROJECTS_TABLE_NAME]

    project_item = await projects_db.get_item({"projectId": item.project_id})
    if not project_item:
        raise ClientResourcesNotFoundError(
            f"Project '{item.project_id}' not found.",
        )

    project = Project.model_validate(project_item)

    archive = await download_project_usecase(
        user=user,
        project=project,
        bucket_name=MEDIA_BUCKET_NAME,
        storage=request.app.state.object_storage,
    )

    return DownloadProjectResponse(
        download_url=archive.download_url,
        expires_in_seconds=archive.expires_in_seconds,
    )
