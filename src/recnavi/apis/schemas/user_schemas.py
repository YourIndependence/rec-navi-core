# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""User API response schemas."""

from pydantic import Field

from recnavi.apis.schemas.base_request_schemas import BaseItemModel
from recnavi.apis.schemas.base_response_schemas import BaseApiResponseModel
from recnavi.core.types.user import User
from recnavi.core.types.user import UserRole


class GetMeResponse(BaseApiResponseModel):
    """Response schema for GET /getMe endpoint."""

    user: User = Field(
        ...,
        description="Current authenticated user information",
    )


class CreateUserRequest(BaseItemModel):
    """Request payload for POST /createUser.

    The group is taken from the caller, never from the payload.
    """

    email: str = Field(..., description="Email address of the new user")
    user_name: str = Field(..., description="Name shown to other members")
    role: UserRole = Field(..., description="'owner' or 'staff'")


class CreateUserResponse(BaseApiResponseModel):
    """Response for POST /createUser."""

    users: list[User] = Field(
        ...,
        description="Users in the caller's group after creation",
    )
