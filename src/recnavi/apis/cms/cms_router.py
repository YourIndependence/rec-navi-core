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
from fastapi import Request

from recnavi.apis.auth.auth import verify_user
from recnavi.apis.schemas.project_schemas import CreateProjectRequest
from recnavi.apis.schemas.project_schemas import CreateProjectResponse
from recnavi.apis.schemas.project_schemas import DeleteProjectRequest
from recnavi.apis.schemas.project_schemas import DeleteProjectResponse
from recnavi.apis.schemas.project_schemas import UpdateProjectRequest
from recnavi.apis.schemas.project_schemas import UpdateProjectResponse
from recnavi.apis.schemas.scene_schemas import GetSceneMastersResponse
from recnavi.apis.schemas.scene_schemas import SceneMasterView
from recnavi.apis.schemas.template_schemas import GetTemplatesResponse
from recnavi.apis.schemas.user_schemas import GetGroupUsersResponse
from recnavi.apis.schemas.user_schemas import GroupUserView
from recnavi.application.project.create_project import create_project_usecase
from recnavi.application.project.delete_project import delete_project_usecase
from recnavi.application.project.update_project import update_project_usecase
from recnavi.application.scene.get_scene_masters import (
    get_scene_masters_usecase,
)
from recnavi.application.scene.get_templates import get_templates_usecase
from recnavi.application.user.get_group_users_usecase import (
    get_group_users_usecase,
)
from recnavi.config.variables import PROJECTS_TABLE_NAME
from recnavi.config.variables import SCENES_TABLE_NAME
from recnavi.config.variables import TEMPLATES_TABLE_NAME
from recnavi.config.variables import USERS_TABLE_NAME
from recnavi.core.types.user import User


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


@cms_router.get("/getGroupUsers")
async def get_group_users_endpoint(
    request: Request,
    user: User = Depends(verify_user),
) -> GetGroupUsersResponse:
    """List all users in the authenticated user's group."""
    users_db = request.app.state.database[USERS_TABLE_NAME]
    users = await get_group_users_usecase(
        users_db=users_db,
        user=user,
    )
    return GetGroupUsersResponse(
        users=[GroupUserView.model_validate(member) for member in users],
    )


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


@cms_router.post("/updateProject")
async def update_project_endpoint(
    request: Request,
    item: UpdateProjectRequest,
    user: User = Depends(verify_user),
) -> UpdateProjectResponse:
    """Update project with optimistic locking."""
    projects_db = request.app.state.database[PROJECTS_TABLE_NAME]

    updated_project = await update_project_usecase(
        projects_db=projects_db,
        project_id=item.project.project_id,
        project_name=item.project.project_name,
        description=item.project.description,
        assigned_user_ids=item.project.assigned_user_ids,
        scenes=item.project.scenes,
        expected_version=item.project.version,
        user=user,
        storage=request.app.state.object_storage,
    )

    return UpdateProjectResponse(project=updated_project)


@cms_router.post("/deleteProject")
async def delete_project_endpoint(
    request: Request,
    item: DeleteProjectRequest,
    user: User = Depends(verify_user),
) -> DeleteProjectResponse:
    """Delete project and associated S3 files."""
    projects_db = request.app.state.database[PROJECTS_TABLE_NAME]

    await delete_project_usecase(
        projects_db=projects_db,
        project_id=item.project_id,
        user=user,
        storage=request.app.state.object_storage,
    )

    return DeleteProjectResponse(project_id=item.project_id)
