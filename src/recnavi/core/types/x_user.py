# Copyright (c) 2025 TOYOTA MOTOR CORPORATION. All rights reserved.
#
# This software is the confidential and proprietary information of
# TOYOTA MOTOR CORPORATION. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# TRUST developer team.

"""user model."""

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import alias_generators


class XUser(BaseModel):
    """load shared history item."""

    model_config = ConfigDict(
        alias_generator=alias_generators.to_camel,
        populate_by_name=True,
        extra="allow",
    )
    id: str = Field(..., description="user unique ID")
    mail: str = Field(..., description="mail string")
    is_admin: bool = Field(..., description="is admin")
