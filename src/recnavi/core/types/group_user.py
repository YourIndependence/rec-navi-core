# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.


"""group user model."""

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


class GroupUser(BaseModel):
    """A user as a member of a group.

    Cognito holds the identity: who this is and how they sign in. What
    they may do and where they belong is stored here, so a change takes
    effect on the next request rather than on the next sign-in.
    """

    model_config = ConfigDict(
        alias_generator=alias_generators.to_camel,
        populate_by_name=True,
    )

    user_id: str = Field(..., description="Identifier of the user")
    user_name: str = Field(..., description="Name shown to other members")
    role: UserRole = Field(..., description="What the user may do")
    group_id: str = Field(..., description="Tenant the user belongs to")
