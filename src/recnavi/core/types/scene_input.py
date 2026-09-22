# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""SceneInput type for update requests (excludes read-only fields)."""

from pydantic import BaseModel
from pydantic import Field


class SceneInput(BaseModel):
    """Scene input from update request (read-only fields excluded)."""

    scene_id: str | None = Field(
        None,
        description="Scene ID (null for new scene)",
    )
    scene_principal: str = Field(..., description="Scene master principal")
    assigned_user_ids: list[str] = Field(
        default_factory=list,
        description="Staff assigned to scene",
    )
