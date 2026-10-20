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
from fastapi import Response

from recnavi.apis.auth.auth import verify_user
from recnavi.apis.schemas.project_schemas import CreateProjectRequest
from recnavi.apis.schemas.project_schemas import CreateProjectResponse
from recnavi.apis.schemas.project_schemas import DeleteProjectRequest
from recnavi.apis.schemas.project_schemas import DeleteProjectResponse
from recnavi.apis.schemas.project_schemas import DownloadProjectRequest
from recnavi.apis.schemas.project_schemas import DownloadProjectResponse
from recnavi.apis.schemas.project_schemas import UpdateProjectRequest
from recnavi.apis.schemas.project_schemas import UpdateProjectResponse
from recnavi.apis.schemas.scene_schemas import GetSceneMastersResponse
from recnavi.apis.schemas.scene_schemas import ReviewSceneRequest
from recnavi.apis.schemas.scene_schemas import ReviewSceneResponse
from recnavi.apis.schemas.scene_schemas import UpdateSceneMasterRequest
from recnavi.apis.schemas.scene_schemas import UpdateSceneMasterResponse
from recnavi.apis.schemas.template_schemas import GetTemplatesResponse
from recnavi.apis.schemas.user_schemas import GetGroupUsersResponse
from recnavi.application.project.create_project import create_project_usecase
from recnavi.application.project.delete_project import delete_project_usecase
from recnavi.application.project.download_project import (
    download_project_usecase,
)
from recnavi.application.project.update_project import update_project_usecase
from recnavi.application.scene.get_scene_masters import (
    get_scene_masters_usecase,
)
from recnavi.application.scene.get_templates import get_templates_usecase
from recnavi.application.scene.review_scene import review_scene_usecase
from recnavi.application.scene.update_scene_master import (
    update_scene_master_usecase,
)
from recnavi.application.user.get_group_users import get_group_users_usecase
from recnavi.config.variables import PROJECTS_TABLE_NAME
from recnavi.config.variables import SCENES_TABLE_NAME
from recnavi.config.variables import TEMPLATES_TABLE_NAME
from recnavi.config.variables import USERS_TABLE_NAME
from recnavi.core.types.project import DOWNLOAD_URL_EXPIRATION_SECONDS
from recnavi.core.types.user import User
from recnavi.core.types.user import UserSummary
from recnavi.exceptions.exceptions import ClientNotFoundError


cms_router = APIRouter(tags=["CMS"])


@cms_router.get(
    "/getSceneMasters",
    response_model=GetSceneMastersResponse,
)
async def get_scene_masters_endpoint(
    request: Request,
    response: Response,
    _user: User = Depends(verify_user),
) -> GetSceneMastersResponse:
    """List all scene masters."""
    scenes_db = request.app.state.database[SCENES_TABLE_NAME]
    scene_masters = await get_scene_masters_usecase(
        scenes_db=scenes_db,
        storage=request.app.state.object_storage,
    )
    response.headers["Cache-Control"] = "no-store"
    return GetSceneMastersResponse(scenes=scene_masters)


@cms_router.get(
    "/getTemplates",
    response_model=GetTemplatesResponse,
)
async def get_templates_endpoint(
    request: Request,
    response: Response,
    _user: User = Depends(verify_user),
) -> GetTemplatesResponse:
    """List all scenes templates."""
    templates_db = request.app.state.database[TEMPLATES_TABLE_NAME]
    templates = await get_templates_usecase(
        templates_db=templates_db,
        storage=request.app.state.object_storage,
    )
    response.headers["Cache-Control"] = "no-store"
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
        users=[
            UserSummary(
                user_id=member.user_id,
                user_name=member.user_name,
                role=member.role,
                group_id=member.group_id,
                profile_image_uri=member.profile_image_uri,
            )
            for member in users
        ],
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


@cms_router.post("/reviewScene")
async def review_scene_endpoint(
    request: Request,
    item: ReviewSceneRequest,
    user: User = Depends(verify_user),
) -> ReviewSceneResponse:
    """Review a scene recording (approved or rejected)."""
    projects_db = request.app.state.database[PROJECTS_TABLE_NAME]

    updated_project = await review_scene_usecase(
        projects_db=projects_db,
        project_id=item.project_id,
        scene_id=item.scene_id,
        result=item.result,
        review_comment=item.comment,
        user=user,
        storage=request.app.state.object_storage,
    )

    return ReviewSceneResponse(project=updated_project)


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


@cms_router.post("/downloadProject")
async def download_project_endpoint(
    request: Request,
    item: DownloadProjectRequest,
    user: User = Depends(verify_user),
) -> DownloadProjectResponse:
    """Create a download archive for the project's owner."""
    archive = await download_project_usecase(
        projects_db=request.app.state.database[PROJECTS_TABLE_NAME],
        project_id=item.project_id,
        user=user,
        storage=request.app.state.object_storage,
    )
    if archive.download_url is None:
        raise ClientNotFoundError("Project not found.")

    return DownloadProjectResponse(
        download_url=archive.download_url,
        expires_in_seconds=DOWNLOAD_URL_EXPIRATION_SECONDS,
    )


@cms_router.post(
    "/updateSceneMaster",
    response_model=UpdateSceneMasterResponse,
)
async def update_scene_master_endpoint(
    request: Request,
    item: UpdateSceneMasterRequest,
    user: User = Depends(verify_user),
) -> UpdateSceneMasterResponse:
    """Create or update scene master."""
    scenes_db = request.app.state.database[SCENES_TABLE_NAME]

    scene_master = await update_scene_master_usecase(
        scenes_db=scenes_db,
        user=user,
        scene_principal=item.scene_principal,
        title=item.title,
        max_duration_seconds=item.max_duration_seconds,
        thumbnail_image=item.thumbnail_image,
        guide_image=item.guide_image,
        storage=request.app.state.object_storage,
    )

    return UpdateSceneMasterResponse(scene_master=scene_master)
