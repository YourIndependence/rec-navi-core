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

from recnavi.apis.schemas.response_schemas import BaseApiResponseModel
from recnavi.core.types.user import User


class GetMeResponse(BaseApiResponseModel):
    """Response schema for GET /getMe endpoint.

    Returns the currently authenticated user and their group ID. The groupId
    is placed at the top level (not duplicated inside user) so the frontend
    can immediately determine which screen to display.
    """

    user: User = Field(
        ...,
        description="Current authenticated user information",
    )
    group_id: str = Field(
        ...,
        description="Group/tenant ID the user belongs to",
    )
