# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Project as returned to clients, with playable URLs instead of keys."""

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import alias_generators

from recnavi.core.types.project import ProjectStatus
from recnavi.core.types.scene import SceneStatus


class SceneView(BaseModel):
    """A scene with presigned playback URLs and no storage keys."""

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
        ...,
        description="How far the scene has progressed",
    )
    video_url: str | None = Field(
        default=None,
        description="Presigned URL of the recorded video. None if not recorded",
    )
    thumbnail_url: str | None = Field(
        default=None,
        description="Presigned URL of the thumbnail. None if not recorded",
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


class ProjectView(BaseModel):
    """A project whose scenes carry presigned playback URLs."""

    model_config = ConfigDict(
        alias_generator=alias_generators.to_camel,
        populate_by_name=True,
    )

    project_id: str = Field(..., description="Identifier of the project")
    project_name: str = Field(..., description="Name shown to the members")
    description: str = Field(
        default="",
        description="Free text of date, place, shop name and notes",
    )
    status: ProjectStatus = Field(
        ...,
        description="How far the project has progressed",
    )
    scenes: list[SceneView] = Field(
        default_factory=list,
        description="Scenes to record in the project",
    )
    owner_user_id: str = Field(
        ...,
        description="Identifier of the account owner who created it",
    )
    assigned_user_ids: list[str] = Field(
        default_factory=list,
        description="Identifiers of the staff who may open the project",
    )
    group_id: str = Field(
        ...,
        description="Identifier of the group that owns the project",
    )
    created_at: str = Field(
        ...,
        description="Datetime the project was created",
    )
    updated_at: str | None = Field(
        default=None,
        description="Datetime the project was last updated",
    )
    version: int = Field(
        default=0,
        description="Optimistic lock version (incremented on each update)",
    )
