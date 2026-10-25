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
from recnavi.core.types.project import ProjectSummary
from recnavi.core.types.scene import Scene


class GetProjectsResponse(BaseApiResponseModel):
    """Response for GET /getProjects."""

    projects: list[ProjectSummary] = Field(
        ...,
        description="Projects of the caller's group",
    )
    next_cursor: str | None = Field(
        None,
        description="Opaque pagination cursor. None if last page.",
    )


class GetMyProjectsResponse(BaseApiResponseModel):
    """Response for GET /getMyProjects."""

    projects: list[ProjectSummary] = Field(
        ...,
        description="Projects assigned to the caller",
    )
    next_cursor: str | None = Field(
        None,
        description="Opaque pagination cursor. May be set on an empty page.",
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
    scenes: list[Scene] = Field(
        default_factory=list,
        description="Complete scene collection after the update. Omitted scenes are deleted; an empty list removes all scenes.",
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


class DownloadProjectRequest(BaseItemModel):
    """Request to archive an approved project."""

    project_id: str = Field(..., min_length=1)


class DownloadProjectResponse(BaseApiResponseModel):
    """Time-limited archive download URL."""

    download_url: str
    expires_in_seconds: int
