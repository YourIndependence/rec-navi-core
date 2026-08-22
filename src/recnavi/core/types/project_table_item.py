# Copyright (c) 2025 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.


"""ProjectTableItem"""

from enum import StrEnum

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import alias_generators


class ProjectStatus(StrEnum):
    """Project progress status."""

    IN_PROGRESS = "in_progress"
    SUBMITTED = "submitted"


class SceneStatus(StrEnum):
    """Scene recording status."""

    NOT_RECORDED = "not_recorded"
    PENDING = "pending"
    REJECT = "reject"
    APPROVE = "approve"


class Scene(BaseModel):
    """Shooting task embedded in a project item."""

    model_config = ConfigDict(
        alias_generator=alias_generators.to_camel,
        populate_by_name=True,
    )

    scene_id: str = Field(..., description="unique id in the project")
    scene_principal: str = Field(..., description="scenes table key")
    status: SceneStatus = Field(
        default=SceneStatus.NOT_RECORDED,
        description="recording status",
    )
    video_key: str | None = Field(
        default=None,
        description="S3 object key of the recorded video",
    )
    thumbnail_key: str | None = Field(
        default=None,
        description="S3 object key of the video thumbnail",
    )
    created_by: str | None = Field(
        default=None,
        description="user id who recorded the video",
    )
    created_at: str | None = Field(
        default=None,
        description="recorded datetime, ISO 8601",
    )
    assigned_at: str | None = Field(
        default=None,
        description="assigned datetime, ISO 8601",
    )
    assigned_user_ids: list[str] = Field(
        default_factory=list,
        description="staff who record this scene",
    )


class ProjectTableItem(BaseModel):
    """projects table item."""

    model_config = ConfigDict(
        alias_generator=alias_generators.to_camel,
        populate_by_name=True,
    )

    project_id: str = Field(..., description="partition key")
    group_id: str = Field(..., description="tenant boundary, GSI1 PK")
    project_name: str = Field(..., description="project name")
    owner_user_id: str = Field(..., description="user id who created")
    created_at: str = Field(..., description="GSI1 SK, ISO 8601")
    description: str = Field(
        default="",
        description="free text of date, place, shop name and notes",
    )
    scenes: list[Scene] = Field(
        default_factory=list,
        description="embedded shooting tasks",
    )
    assigned_user_ids: list[str] = Field(
        default_factory=list,
        description="staff who may open this project",
    )
    status: ProjectStatus = Field(
        default=ProjectStatus.IN_PROGRESS,
        description="progress status",
    )
