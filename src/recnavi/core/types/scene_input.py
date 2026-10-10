# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""SceneInput type for update requests (excludes read-only fields)."""

from uuid import uuid4

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import alias_generators


class SceneInput(BaseModel):
    """Scene input from update request (read-only fields excluded)."""

    model_config = ConfigDict(
        alias_generator=alias_generators.to_camel,
        populate_by_name=True,
    )

    scene_id: str = Field(
        default_factory=lambda: str(uuid4()),
        description="Scene ID (omit for a new scene; one is issued)",
    )
    scene_principal: str = Field(..., description="Scene master principal")
    assigned_user_ids: list[str] = Field(
        default_factory=list,
        description="Staff assigned to scene",
    )
