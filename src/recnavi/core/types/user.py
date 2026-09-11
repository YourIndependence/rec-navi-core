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
    """Someone who uses the service, on behalf of one tenant.

    Cognito holds the identity: who this is and how they sign in. What
    they may do and which tenant they belong to is stored here, so a
    change takes effect on the next request rather than on the next
    sign-in. Cognito groups carry no attributes of their own, which is
    why the tenant is not kept there.
    """

    model_config = ConfigDict(
        alias_generator=alias_generators.to_camel,
        populate_by_name=True,
    )

    user_id: str = Field(..., description="Identifier of the user")
    user_name: str = Field(..., description="Name shown to other members")
    role: UserRole = Field(..., description="What the user may do")
    group_id: str = Field(..., description="Tenant the user belongs to")
