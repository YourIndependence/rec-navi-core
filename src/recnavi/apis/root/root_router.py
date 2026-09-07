# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Root router"""

import time

from fastapi import APIRouter
from fastapi import Depends
from fastapi import Request

from recnavi.apis.auth.auth import get_authenticated_user
from recnavi.apis.auth.auth import verify_user
from recnavi.apis.schemas.response_schemas import GreetingResponse
from recnavi.apis.schemas.user_schemas import GetMeResponse
from recnavi.config.variables import ENV
from recnavi.core.types.group_user import GroupUser
from recnavi.core.types.x_user import XUser


root_router = APIRouter(tags=["Root"])


@root_router.get("/health")
def health_check():
    """Health check api."""
    return {"status": "ok"}


@root_router.get("/greeting")
async def greeting():
    """Test API endpoint **without** authentication."""
    return {
        "status": "ok",
        "timestamp": int(time.time()),
        "environment": ENV,
    }


@root_router.post("/greetingMe", response_model=GreetingResponse)
async def greeting_me(
    request: Request,
    x_user: XUser = Depends(verify_user),
) -> GreetingResponse:
    """Task status check API for pooling."""
    _ = request
    return GreetingResponse(x_user=x_user)


@root_router.get("/getMe", response_model=GetMeResponse)
async def get_me(
    authenticated_user: GroupUser = Depends(get_authenticated_user),
) -> GetMeResponse:
    """Return the signed-in user and the tenant they belong to."""
    return GetMeResponse.from_group_user(authenticated_user)
