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

from recnavi.apis.auth.auth import verify_user
from recnavi.apis.schemas.user_schemas import GetMeResponse
from recnavi.config.variables import ENV
from recnavi.core.types.user import User


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


@root_router.get("/getMe")
async def get_me(
    user: User = Depends(verify_user),
) -> GetMeResponse:
    """Get current authenticated user."""
    return GetMeResponse(user=user, group_id=user.group_id)
