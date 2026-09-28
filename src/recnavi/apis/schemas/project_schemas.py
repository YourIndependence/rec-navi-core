# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Project-related API schemas."""

from pydantic import Field

from recnavi.apis.schemas.base_response_schemas import BaseApiResponseModel
from recnavi.core.types.project import Project


class GetProjectsResponse(BaseApiResponseModel):
    """Response for GET /getProjects."""

    projects: list[Project] = Field(
        ...,
        description="Projects in descending order by creation date",
    )
    next_cursor: str | None = Field(
        None,
        description="Opaque pagination cursor. None if last page.",
    )


class GetProjectRequest(BaseApiResponseModel):
    """Request payload for POST /getProject."""

    project_id: str = Field(..., description="Project ID to retrieve")


class GetProjectResponse(BaseApiResponseModel):
    """Response for POST /getProject."""

    status: str = Field(default="ok", description="Response status")
    project: Project = Field(..., description="Project with all scenes")


class CreateProjectRequest(BaseApiResponseModel):
    """Request payload for POST /createProject."""

    project_name: str = Field(..., description="Name shown to members")
    description: str = Field(default="", description="Free text notes")
    scene_principals: list[str] = Field(
        ...,
        description="Scene principals expanded by client",
    )
    assigned_user_ids: list[str] = Field(
        default_factory=list,
        description="Staff assigned to the project",
    )


class CreateProjectResponse(BaseApiResponseModel):
    """Response for POST /createProject."""

    project: Project = Field(..., description="Created project")
