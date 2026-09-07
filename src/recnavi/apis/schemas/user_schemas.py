# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.


"""user api schemas."""

from pydantic import Field

from recnavi.apis.schemas.request_schemas import BaseItemModel
from recnavi.apis.schemas.response_schemas import BaseApiResponseModel
from recnavi.core.types.group_user import GroupUser
from recnavi.core.types.group_user import UserRole


class GroupUserView(BaseItemModel):
    """A member of a group as the client sees it.

    The tenant is not repeated on every member. A caller only ever sees
    the members of its own group, and getMe names the tenant once.
    """

    user_id: str = Field(..., description="Identifier of the user")
    user_name: str = Field(..., description="Name shown to other members")
    role: UserRole = Field(..., description="What the user may do")

    @classmethod
    def from_group_user(cls, user: GroupUser) -> "GroupUserView":
        """Show only what the client is meant to see."""
        return cls(
            user_id=user.user_id,
            user_name=user.user_name,
            role=user.role,
        )


class GetMeResponse(BaseApiResponseModel):
    """getMe API response model."""

    user: GroupUserView = Field(..., description="The signed-in user")
    group_id: str = Field(..., description="Tenant the user belongs to")

    @classmethod
    def from_group_user(cls, user: GroupUser) -> "GetMeResponse":
        """Build the response from the domain object."""
        return cls(
            user=GroupUserView.from_group_user(user),
            group_id=user.group_id,
        )
