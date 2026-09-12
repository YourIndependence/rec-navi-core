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
from recnavi.apis.schemas.scene_schemas import GetSceneMastersResponse
from recnavi.apis.schemas.scene_schemas import SceneMasterView
from recnavi.config.variables import SCENES_TABLE_NAME
from recnavi.core.scene.scene_master import get_scene_masters
from recnavi.core.types.user import User


cms_router = APIRouter(tags=["CMS"])


@cms_router.get("/getSceneMasters")
async def get_scene_masters_endpoint(
    request: Request,
    _user: User = Depends(verify_user),
) -> GetSceneMastersResponse:
    """List all scene masters.

    Returns all scene masters from the database. The scenes table is small
    (dozens of rows, shared across all tenants), so a full scan is acceptable.

    This endpoint requires a valid authentication token.

    Args:
        request: FastAPI request object.
        _user: Authenticated user (validates token but not used in logic).

    Returns:
        GetSceneMastersResponse with list of all scene masters.

    """
    scenes_db = request.app.state.database[SCENES_TABLE_NAME]
    scene_masters = await get_scene_masters(scenes_db=scenes_db)

    scene_views = [
        SceneMasterView(
            scene_principal=sm.scene_principal,
            title=sm.title,
            max_duration_seconds=sm.max_duration_seconds,
        )
        for sm in scene_masters
    ]

    return GetSceneMastersResponse(scenes=scene_views)
