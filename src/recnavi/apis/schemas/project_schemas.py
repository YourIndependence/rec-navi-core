# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Project-related API schemas."""

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import alias_generators

from recnavi.core.types.project import ProjectStatus


class ProjectSummaryView(BaseModel):
    """Project summary for list view.

    Excludes scenes array to keep response lightweight. Scenes are not
    included in GSI1 projection and are not needed for list display.
    """

    model_config = ConfigDict(
        alias_generator=alias_generators.to_camel,
        populate_by_name=True,
    )

    project_id: str = Field(..., description="Identifier of the project")
    project_name: str = Field(..., description="Name shown to members")
    description: str = Field(..., description="Free text notes")
    owner_user_id: str = Field(..., description="Owner who created it")
    created_at: str = Field(..., description="Creation datetime")
    status: ProjectStatus = Field(..., description="Progress status")


class GetProjectsResponse(BaseModel):
    """Response for GET /getProjects."""

    model_config = ConfigDict(
        alias_generator=alias_generators.to_camel,
        populate_by_name=True,
    )

    status: str = Field(default="ok", description="Response status")
    projects: list[ProjectSummaryView] = Field(
        ...,
        description="Projects in descending order by creation date",
    )
    next_cursor: str | None = Field(
        None,
        description="Opaque pagination cursor. None if last page.",
    )


class GetProjectRequest(BaseModel):
    """Request payload for POST /getProject."""

    model_config = ConfigDict(
        alias_generator=alias_generators.to_camel,
        populate_by_name=True,
    )

    project_id: str = Field(..., description="Project ID to retrieve")


class SceneView(BaseModel):
    """Scene view with presigned URLs for video and thumbnail."""

    model_config = ConfigDict(
        alias_generator=alias_generators.to_camel,
        populate_by_name=True,
    )

    scene_id: str = Field(..., description="Identifier of the scene")
    scene_principal: str = Field(..., description="Scene master principal")
    status: str = Field(..., description="Scene recording status")
    video_url: str | None = Field(
        None,
        description="Presigned URL for video (valid 1 hour)",
    )
    thumbnail_url: str | None = Field(
        None,
        description="Presigned URL for thumbnail (valid 1 hour)",
    )
    created_by: str | None = Field(
        None,
        description="Staff who recorded the video",
    )
    created_at: str | None = Field(
        None,
        description="Datetime the video was recorded",
    )
    assigned_at: str | None = Field(
        None,
        description="Datetime the scene was assigned",
    )
    assigned_user_ids: list[str] = Field(
        default_factory=list,
        description="Staff assigned to record the scene",
    )


class ProjectView(BaseModel):
    """Project view with all scenes and presigned URLs."""

    model_config = ConfigDict(
        alias_generator=alias_generators.to_camel,
        populate_by_name=True,
    )

    project_id: str = Field(..., description="Identifier of the project")
    group_id: str = Field(..., description="Tenant the project belongs to")
    project_name: str = Field(..., description="Name shown to members")
    description: str = Field(..., description="Free text notes")
    owner_user_id: str = Field(..., description="Owner who created it")
    assigned_user_ids: list[str] = Field(
        default_factory=list,
        description="Staff assigned to the project",
    )
    created_at: str = Field(..., description="Creation datetime")
    updated_at: str = Field(..., description="Last update datetime")
    status: ProjectStatus = Field(..., description="Progress status")
    version: int = Field(..., description="Optimistic lock version")
    scenes: list[SceneView] = Field(
        default_factory=list,
        description="All scenes in the project with presigned URLs",
    )


class GetProjectResponse(BaseModel):
    """Response for POST /getProject."""

    model_config = ConfigDict(
        alias_generator=alias_generators.to_camel,
        populate_by_name=True,
    )

    status: str = Field(default="ok", description="Response status")
    project: ProjectView = Field(..., description="Project with all scenes")
