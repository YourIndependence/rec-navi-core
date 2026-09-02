# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.


"""Master router"""

from fastapi import APIRouter
from fastapi import Depends

from recnavi.apis.auth.auth import get_authenticated_user
from recnavi.apis.dependencies import get_scene_master_repository
from recnavi.apis.dependencies import get_scenes_template_repository
from recnavi.apis.schemas.master_schemas import GetSceneMastersResponse
from recnavi.apis.schemas.master_schemas import GetTemplatesResponse
from recnavi.application.master.list_scene_masters import list_scene_masters
from recnavi.application.master.list_scenes_templates import (
    list_scenes_templates,
)
from recnavi.core.repositories.scene_master_repository import (
    BaseSceneMasterRepository,
)
from recnavi.core.repositories.scenes_template_repository import (
    BaseScenesTemplateRepository,
)


master_router = APIRouter(tags=["Master"])


@master_router.get(
    "/getSceneMasters",
    response_model=GetSceneMastersResponse,
    dependencies=[Depends(get_authenticated_user)],
)
async def get_scene_masters(
    repository: BaseSceneMasterRepository = Depends(
        get_scene_master_repository,
    ),
) -> GetSceneMastersResponse:
    """Return every scene master."""
    masters = await list_scene_masters(repository=repository)
    return GetSceneMastersResponse.from_scene_masters(masters)


@master_router.get(
    "/getTemplates",
    response_model=GetTemplatesResponse,
    dependencies=[Depends(get_authenticated_user)],
)
async def get_templates(
    repository: BaseScenesTemplateRepository = Depends(
        get_scenes_template_repository,
    ),
) -> GetTemplatesResponse:
    """Return every scenes template."""
    templates = await list_scenes_templates(repository=repository)
    return GetTemplatesResponse.from_scenes_templates(templates)
