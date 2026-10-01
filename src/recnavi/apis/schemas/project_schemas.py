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

from recnavi.apis.schemas.base_request_schemas import BaseItemModel
from recnavi.apis.schemas.base_response_schemas import BaseApiResponseModel
from recnavi.core.types.project import Project
from recnavi.core.types.project import ProjectStatus


class ProjectSummaryView(BaseModel):
    """Project summary for list views (excludes scenes array)."""

    model_config = ConfigDict(
        alias_generator=alias_generators.to_camel,
        populate_by_name=True,
    )

    project_id: str = Field(..., description="Project ID")
    project_name: str = Field(..., description="Name shown to members")
    description: str = Field(..., description="Free text notes")
    owner_user_id: str = Field(..., description="Owner who created it")
    created_at: str = Field(..., description="Creation timestamp")
    status: ProjectStatus = Field(..., description="Project status")


class GetProjectsResponse(BaseApiResponseModel):
    """Response for GET /getProjects."""

    projects: list[ProjectSummaryView] = Field(
        ...,
        description="Projects in descending order by creation date",
    )
    next_cursor: str | None = Field(
        None,
        description="Opaque pagination cursor. None if last page.",
    )


class GetProjectRequest(BaseItemModel):
    """Request payload for POST /getProject."""

    project_id: str = Field(..., description="Project ID to retrieve")


class GetProjectResponse(BaseApiResponseModel):
    """Response for POST /getProject."""

    project: Project = Field(..., description="Project with all scenes")


class CreateProjectRequest(BaseItemModel):
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


class SceneInput(BaseModel):
    """Scene input for update request (read-only fields excluded)."""

    model_config = ConfigDict(
        alias_generator=alias_generators.to_camel,
        populate_by_name=True,
    )

    scene_id: str | None = Field(
        None,
        description="Scene ID (null for new scene)",
    )
    scene_principal: str = Field(..., description="Scene master principal")
    assigned_user_ids: list[str] = Field(
        default_factory=list,
        description="Staff assigned to scene",
    )


class ProjectInput(BaseModel):
    """Project input for update."""

    model_config = ConfigDict(
        alias_generator=alias_generators.to_camel,
        populate_by_name=True,
    )

    project_id: str = Field(..., description="Project ID to update")
    project_name: str = Field(..., description="Project name")
    description: str = Field(..., description="Project description")
    assigned_user_ids: list[str] = Field(
        default_factory=list,
        description="Staff assigned to project",
    )
    scenes: list[SceneInput] = Field(
        default_factory=list,
        description="Scenes array",
    )
    version: int = Field(
        ...,
        description="Expected version for optimistic locking",
    )


class UpdateProjectRequest(BaseItemModel):
    """Request payload for POST /updateProject."""

    project: ProjectInput = Field(..., description="Project data to update")


class UpdateProjectResponse(BaseApiResponseModel):
    """Response for POST /updateProject."""

    project: Project = Field(..., description="Updated project")


class DeleteProjectRequest(BaseItemModel):
    """Request payload for POST /deleteProject."""

    project_id: str = Field(..., description="Project ID to delete")


class DeleteProjectResponse(BaseApiResponseModel):
    """Response for POST /deleteProject."""

    project_id: str = Field(..., description="Deleted project ID")
