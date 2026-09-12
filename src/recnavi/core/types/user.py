# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.


"""User"""

from enum import StrEnum

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import alias_generators


class UserRole(StrEnum):
    """What a user is allowed to do."""

    ADMIN = "admin"
    OWNER = "owner"
    STAFF = "staff"


class User(BaseModel):
    """user"""

    model_config = ConfigDict(
        alias_generator=alias_generators.to_camel,
        populate_by_name=True,
    )

    user_id: str = Field(..., description="Identifier of the user")
    user_name: str = Field(..., description="Name shown to other members")
    role: UserRole = Field(..., description="What the user may do")
    group_id: str = Field(..., description="Tenant the user belongs to")
