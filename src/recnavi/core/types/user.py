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
    """A member of a group."""

    model_config = ConfigDict(
        alias_generator=alias_generators.to_camel,
        populate_by_name=True,
    )

    user_id: str = Field(..., description="Identifier of the user")
    group_id: str = Field(
        ...,
        description="Identifier of the group the user belongs to",
    )
    user_name: str = Field(..., description="Name shown to the members")
    role: UserRole = Field(..., description="What the user is allowed to do")
