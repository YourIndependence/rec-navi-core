# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.


"""UserTableItem"""

from enum import Enum

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import alias_generators


class UserRole(str, Enum):
    """user role enum."""

    ADMIN = "admin"
    OWNER = "owner"
    STAFF = "staff"


class UserTableItem(BaseModel):
    """users table item."""

    model_config = ConfigDict(
        alias_generator=alias_generators.to_camel,
        populate_by_name=True,
    )

    user_id: str = Field(..., description="partition key")
    group_id: str = Field(..., description="tenant boundary, GSI1 PK")
    user_name: str = Field(..., description="display name")
    role: UserRole = Field(..., description="authorization role")
