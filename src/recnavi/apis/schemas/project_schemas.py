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

from recnavi.core.types.project import Project
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


class GetProjectResponse(BaseModel):
    """Response for POST /getProject."""

    model_config = ConfigDict(
        alias_generator=alias_generators.to_camel,
        populate_by_name=True,
    )

    status: str = Field(default="ok", description="Response status")
    project: Project = Field(..., description="Project with all scenes")
