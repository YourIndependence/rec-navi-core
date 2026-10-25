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

from recnavi.apis.schemas.base_response_schemas import BaseApiResponseModel
from recnavi.core.types.user import User
from recnavi.core.types.user import UserSummary


class GetMeResponse(BaseApiResponseModel):
    """Response schema for GET /getMe endpoint."""

    user: User = Field(
        ...,
        description="Current authenticated user information",
    )
    group_id: str = Field(
        ...,
        description="Group ID the current user belongs to",
    )


class GetGroupUsersResponse(BaseApiResponseModel):
    """Response schema for GET /getGroupUsers endpoint."""

    users: list[UserSummary] = Field(
        ...,
        description="All users in the authenticated user's group",
    )
