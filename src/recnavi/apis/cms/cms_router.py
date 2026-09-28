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
from recnavi.apis.schemas.project_schemas import DeleteProjectRequest
from recnavi.apis.schemas.project_schemas import DeleteProjectResponse
from recnavi.apis.schemas.project_schemas import GetProjectRequest
from recnavi.apis.schemas.project_schemas import GetProjectResponse
from recnavi.apis.schemas.project_schemas import GetProjectsResponse
from recnavi.apis.schemas.project_schemas import SubmitProjectRequest
from recnavi.apis.schemas.project_schemas import SubmitProjectResponse
from recnavi.apis.schemas.project_schemas import UpdateProjectRequest
from recnavi.apis.schemas.project_schemas import UpdateProjectResponse
from recnavi.apis.schemas.scene_schemas import GetSceneMastersResponse
from recnavi.apis.schemas.scene_schemas import ReviewSceneRequest
from recnavi.apis.schemas.scene_schemas import ReviewSceneResponse
from recnavi.apis.schemas.scene_schemas import SceneMasterView
from recnavi.apis.schemas.template_schemas import GetTemplatesResponse
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


@cms_router.post("/updateProject")
async def update_project_endpoint(
    request: Request,
    item: UpdateProjectRequest,
    user: User = Depends(verify_user),
) -> UpdateProjectResponse:
    """Update project with optimistic locking."""
    from recnavi.application.project.update_project_usecase import (
        update_project_usecase,
    )
    from recnavi.core.types.scene_input import SceneInput as CoreSceneInput

    projects_db = request.app.state.database[PROJECTS_TABLE_NAME]

    core_scene_inputs = [
        CoreSceneInput(
            scene_id=scene.scene_id,
            scene_principal=scene.scene_principal,
            assigned_user_ids=scene.assigned_user_ids,
        )
        for scene in item.project.scenes
    ]

    updated_project = await update_project_usecase(
        projects_db=projects_db,
        project_id=item.project.project_id,
        project_name=item.project.project_name,
        description=item.project.description,
        assigned_user_ids=item.project.assigned_user_ids,
        scenes=core_scene_inputs,
        expected_version=item.project.version,
        user=user,
    )

    return UpdateProjectResponse(project=updated_project)


@cms_router.post("/deleteProject")
async def delete_project_endpoint(
    request: Request,
    item: DeleteProjectRequest,
    user: User = Depends(verify_user),
) -> DeleteProjectResponse:
    """Delete a project and its recordings."""
    from recnavi.application.project.delete_project_usecase import (
        delete_project_usecase,
    )

    projects_db = request.app.state.database[PROJECTS_TABLE_NAME]

    project_id = await delete_project_usecase(
        projects_db=projects_db,
        project_id=item.project_id,
        user=user,
        video_bucket_name=MEDIA_BUCKET_NAME,
    )

    return DeleteProjectResponse(project_id=project_id)


@cms_router.post("/reviewScene")
async def review_scene_endpoint(
    request: Request,
    item: ReviewSceneRequest,
    user: User = Depends(verify_user),
) -> ReviewSceneResponse:
    """Review a recorded scene (owner-only operation)."""
    from recnavi.application.scene.review_scene_usecase import (
        review_scene_usecase,
    )

    projects_db = request.app.state.database[PROJECTS_TABLE_NAME]

    updated_project = await review_scene_usecase(
        projects_db=projects_db,
        project_id=item.project_id,
        scene_id=item.scene_id,
        result=item.result,
        review_comment=item.comment,
        user=user,
    )

    return ReviewSceneResponse(project=updated_project)
