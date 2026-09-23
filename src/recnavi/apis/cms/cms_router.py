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
from recnavi.apis.schemas.project_schemas import DownloadProjectRequest
from recnavi.apis.schemas.project_schemas import DownloadProjectResponse
from recnavi.apis.schemas.scene_schemas import GetSceneMastersResponse
from recnavi.apis.schemas.scene_schemas import SceneMasterView
from recnavi.apis.schemas.template_schemas import GetTemplatesResponse
from recnavi.application.project import download_project_usecase
from recnavi.application.scene.get_scene_masters_usecase import (
    get_scene_masters_usecase,
)
from recnavi.application.scene.get_templates_usecase import (
    get_templates_usecase,
)
from recnavi.config.variables import PROJECTS_TABLE_NAME
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
    "/downloadProject",
    response_model=DownloadProjectResponse,
)
async def download_project_endpoint(
    request: Request,
    body: DownloadProjectRequest,
    user: User = Depends(verify_user),
) -> DownloadProjectResponse:
    """Download approved project as zip archive."""
    projects_db = request.app.state.database[PROJECTS_TABLE_NAME]

    # Get project from database
    project_item = await projects_db.get_item({"projectId": body.project_id})
    if not project_item:
        from recnavi.exceptions.exceptions import ClientResourcesNotFoundError

        raise ClientResourcesNotFoundError(
            f"Project '{body.project_id}' not found.",
        )

    # Convert to Project type
    from recnavi.core.types.project import Project

    project = Project.model_validate(project_item)

    # Import S3 functions locally (ARCH-012 compliance)
    from recnavi.infrastructure.s3.s3_client import download_object
    from recnavi.infrastructure.s3.s3_client import generate_presigned_url

    # Helper for S3 upload
    async def upload_zip_to_s3(
        *,
        bucket_name: str,
        object_key: str,
        zip_bytes: bytes,
    ) -> None:
        """Upload zip bytes to S3."""
        import base64

        from recnavi.infrastructure.s3.s3_client import upload_base64

        base64_data = base64.b64encode(zip_bytes).decode("utf-8")
        await upload_base64(
            bucket_name=bucket_name,
            object_key=object_key,
            base64_data=base64_data,
            content_type="application/zip",
        )

    # Call use case
    presigned_url = await download_project_usecase(
        user=user,
        project=project,
        bucket_name=VIDEO_BUCKET_NAME,
        download_object_fn=download_object,
        generate_presigned_url_fn=generate_presigned_url,
        upload_zip_fn=upload_zip_to_s3,
    )

    return DownloadProjectResponse(download_url=presigned_url)
