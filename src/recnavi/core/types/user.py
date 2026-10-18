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


class UserSummary(BaseModel):
    """Public user information for member selection."""

    model_config = ConfigDict(
        alias_generator=alias_generators.to_camel,
        populate_by_name=True,
    )

    user_id: str = Field(..., description="Identifier of the user")
    user_name: str = Field(..., description="Name shown to other members")
    role: UserRole = Field(..., description="What the user may do")


class User(UserSummary):
    """User details and authorization context."""

    group_id: str = Field(..., description="Tenant the user belongs to")
    email: str | None = Field(
        default=None,
        description="Email address of the user",
    )
    phone_number: str | None = Field(
        default=None,
        description="Phone number of the user",
    )
    birthday: str | None = Field(
        default=None,
        description="Birthday in YYYY-MM-DD format",
    )
    profile_image_uri: str | None = Field(
        default=None,
        description="S3 URI of the user's profile image",
    )

    def can_act_as(self, role: UserRole) -> bool:
        """Return whether this user's role includes the requested role."""
        role_rank = {
            UserRole.STAFF: 1,
            UserRole.OWNER: 2,
            UserRole.ADMIN: 3,
        }
        return role_rank[self.role] >= role_rank[role]
