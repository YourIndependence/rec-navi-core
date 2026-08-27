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

from recnavi.apis.schemas.response_schemas import BaseApiResponseModel
from recnavi.core.types.group_user import GroupUser


class GetMeResponse(BaseApiResponseModel):
    """getMe API response model."""

    user: GroupUser = Field(..., description="The signed-in user")
    group_id: str = Field(..., description="Tenant the user belongs to")
