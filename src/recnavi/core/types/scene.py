# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.


"""Scene"""

from enum import StrEnum

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import alias_generators


class SceneStatus(StrEnum):
    """Scene recording status."""

    NOT_RECORDED = "not_recorded"
    PENDING = "pending"
    REJECT = "reject"
    APPROVE = "approve"


class Scene(BaseModel):
    """A single shot to record in a project."""

    model_config = ConfigDict(
        alias_generator=alias_generators.to_camel,
        populate_by_name=True,
    )

    scene_id: str = Field(..., description="Identifier of the scene")
    scene_principal: str = Field(
        ...,
        description="Inherited scene master principal",
    )
    status: SceneStatus = Field(
        default=SceneStatus.NOT_RECORDED,
        description="How far the scene has progressed",
    )
    video_key: str | None = Field(
        default=None,
        description="Location of the recorded video",
    )
    thumbnail_key: str | None = Field(
        default=None,
        description="Location of the thumbnail of the recorded video",
    )
    created_by: str | None = Field(
        default=None,
        description="Identifier of the staff who recorded the video",
    )
    created_at: str | None = Field(
        default=None,
        description="Datetime the video was recorded",
    )
    assigned_at: str | None = Field(
        default=None,
        description="Datetime the scene was assigned",
    )
    assigned_user_ids: list[str] = Field(
        default_factory=list,
        description="Identifiers of the staff who record the scene",
    )
