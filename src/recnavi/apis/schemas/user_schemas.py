# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""User API response schemas."""

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import alias_generators

from recnavi.apis.schemas.base_response_schemas import BaseApiResponseModel
from recnavi.core.types.user import User
from recnavi.core.types.user import UserRole


class GetMeResponse(BaseApiResponseModel):
    """Response schema for GET /getMe endpoint."""

    user: User = Field(
        ...,
        description="Current authenticated user information",
    )


class GroupUserView(BaseModel):
    """Public member information for assignment selection."""

    model_config = ConfigDict(
        alias_generator=alias_generators.to_camel,
        populate_by_name=True,
        from_attributes=True,
    )

    user_id: str
    user_name: str
    role: UserRole


class GetGroupUsersResponse(BaseApiResponseModel):
    """Response schema for GET /getGroupUsers endpoint."""

    users: list[GroupUserView] = Field(
        ...,
        description="All users in the authenticated user's group",
    )
