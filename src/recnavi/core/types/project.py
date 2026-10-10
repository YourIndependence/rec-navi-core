# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.


"""Project"""

from enum import StrEnum

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import alias_generators

from recnavi.core.types.scene import Scene
from recnavi.core.types.user import User


class ProjectStatus(StrEnum):
    """Project progress status."""

    IN_PROGRESS = "in_progress"
    SUBMITTED = "submitted"


class ProjectSummary(BaseModel):
    """A project without scenes, used by list endpoints."""

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
    owner_user_id: str = Field(
        ...,
        description="Identifier of the account owner who created it",
    )
    created_at: str = Field(
        ...,
        description="Datetime the project was created",
    )
    status: ProjectStatus = Field(
        default=ProjectStatus.IN_PROGRESS,
        description="How far the project has progressed",
    )


class Project(BaseModel):
    """A shooting job an account owner hands to staff."""

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
        default=ProjectStatus.IN_PROGRESS,
        description="How far the project has progressed",
    )
    scenes: list[Scene] = Field(
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

    def is_accessible(self, *, user: User) -> bool:
        """Check if user can access this project."""
        if self.group_id != user.group_id:
            return False

        is_owner = self.owner_user_id == user.user_id
        is_assigned_staff = user.user_id in self.assigned_user_ids

        return is_owner or is_assigned_staff
