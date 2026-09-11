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
from fastapi import Request

from recnavi.apis.auth.auth import decode_token
from recnavi.apis.schemas.user_schemas import GetMeResponse
from recnavi.application.user.get_me import get_me_use_case
from recnavi.config.variables import ENV
from recnavi.config.variables import USERS_TABLE_NAME


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
async def get_me(request: Request) -> GetMeResponse:
    """Get current authenticated user.

    Returns the currently signed-in user's information based on their
    verified JWT token. The role and groupId are read from the users
    table in DynamoDB, not from Cognito claims, so changes take effect
    immediately without requiring re-authentication.

    Returns:
        GetMeResponse with user information and groupId.

    Raises:
        ClientPermissionError (401): Token missing, invalid, or expired.
        ClientAuthorizationError (403): Valid token but user not in database,
            or user has invalid role.

    """
    payload = await decode_token(request)
    sub = payload["sub"]

    user_db = request.app.state.database[USERS_TABLE_NAME]
    user = await get_me_use_case(sub=sub, user_db=user_db)

    return GetMeResponse(user=user, group_id=user.group_id)
