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

from recnavi.apis.auth.auth import verify_admin
from recnavi.apis.auth.auth import verify_user
from recnavi.apis.schemas.project_schemas import DownloadProjectRequest
from recnavi.apis.schemas.project_schemas import DownloadProjectResponse
from recnavi.apis.schemas.scene_schemas import GetSceneMastersResponse
from recnavi.apis.schemas.scene_schemas import SceneMasterView
from recnavi.apis.schemas.scene_schemas import UpdateSceneRequest
from recnavi.apis.schemas.scene_schemas import UpdateSceneResponse
from recnavi.apis.schemas.template_schemas import GetTemplatesResponse
from recnavi.application.project import download_project_usecase
from recnavi.application.scene.get_scene_masters_usecase import (
    get_scene_masters_usecase,
)
from recnavi.application.scene.get_templates_usecase import (
    get_templates_usecase,
)
from recnavi.application.scene.update_scene_usecase import update_scene_usecase
from recnavi.config.variables import PROJECTS_TABLE_NAME
from recnavi.config.variables import SCENE_IMAGES_BUCKET_NAME
from recnavi.config.variables import SCENES_TABLE_NAME
from recnavi.config.variables import TEMPLATES_TABLE_NAME
from recnavi.config.variables import VIDEO_BUCKET_NAME
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
    response_model=GetTemplatesResponse,
)
async def get_templates_endpoint(
    request: Request,
    _user: User = Depends(verify_user),
) -> GetTemplatesResponse:
    """List all scenes templates."""
    templates_db = request.app.state.database[TEMPLATES_TABLE_NAME]
    templates = await get_templates_usecase(templates_db=templates_db)
    return GetTemplatesResponse(templates=templates)


@cms_router.post(
    "/updateScene",
    response_model=UpdateSceneResponse,
)
async def update_scene_endpoint(
    request: Request,
    item: UpdateSceneRequest,
    _user: User = Depends(verify_admin),
) -> UpdateSceneResponse:
    """Create or update scene master (admin-only)."""
    scenes_db = request.app.state.database[SCENES_TABLE_NAME]

    scenes = await update_scene_usecase(
        scenes_db=scenes_db,
        scene_principal=item.scene_principal,
        title=item.title,
        max_duration_seconds=item.max_duration_seconds,
        example_image=item.example_image,
        guide_image=item.guide_image,
        bucket_name=SCENE_IMAGES_BUCKET_NAME,
    )

    scene_views = [
        SceneMasterView(
            scene_principal=sm.scene_principal,
            title=sm.title,
            max_duration_seconds=sm.max_duration_seconds,
        )
        for sm in scenes
    ]

    return UpdateSceneResponse(scenes=scene_views)


@cms_router.post(
    "/downloadProject",
    response_model=DownloadProjectResponse,
)
async def download_project_endpoint(
    request: Request,
    body: DownloadProjectRequest,
    user: User = Depends(verify_user),
) -> DownloadProjectResponse:
    """Download approved project as zip archive."""
    from recnavi.core.types.project import Project
    from recnavi.exceptions.exceptions import ClientResourcesNotFoundError

    projects_db = request.app.state.database[PROJECTS_TABLE_NAME]

    project_item = await projects_db.get_item({"projectId": body.project_id})
    if not project_item:
        raise ClientResourcesNotFoundError(
            f"Project '{body.project_id}' not found.",
        )

    project = Project.model_validate(project_item)

    presigned_url = await download_project_usecase(
        user=user,
        project=project,
        bucket_name=VIDEO_BUCKET_NAME,
    )

    return DownloadProjectResponse(download_url=presigned_url)
