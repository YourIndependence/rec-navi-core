# Copyright (c) 2025 YourIndependence. All rights reserved.
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
    STAFF = "staff"


class Config(BaseModel):
    """user config object."""

    model_config = ConfigDict(
        alias_generator=alias_generators.to_camel,
        populate_by_name=True,
    )

    user_id: str = Field(..., description="user id")
    group_idd: str = Field(..., description="user group id")
    user_name: str = Field(..., description="user name")
    role: UserRole
