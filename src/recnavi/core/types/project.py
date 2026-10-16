# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.


"""Project"""

from datetime import UTC
from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import alias_generators

from recnavi.core.types.scene import Scene
from recnavi.core.types.scene import SceneView
from recnavi.core.types.user import User
from recnavi.core.types.user import UserRole
from recnavi.exceptions.exceptions import ClientNotFoundError


class ProjectStatus(StrEnum):
    """Project progress status."""

    IN_PROGRESS = "in_progress"
    SUBMITTED = "submitted"


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
    scenes: list[Scene | SceneView] = Field(
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

    def validate_permission(
        self,
        *,
        user: User,
        as_role: UserRole,
    ) -> bool:
        """Return whether the user can access this project as the given role."""
        if not user.can_act_as(as_role):
            return False

        match as_role:
            case UserRole.STAFF:
                return (
                    user.user_id == self.owner_user_id
                    or user.user_id in self.assigned_user_ids
                )
            case UserRole.OWNER:
                return self.owner_user_id == user.user_id
            case UserRole.ADMIN:
                return True

    def update_scene(self, scene: Scene) -> None:
        """Replace a scene by ID and advance the project version."""
        self._update_scene_impl(scene)
        self.increment_version()

    def _update_scene_impl(self, scene: Scene) -> None:
        """Replace a scene without changing the project version."""
        for index, current_scene in enumerate(self.scenes):
            if current_scene.scene_id == scene.scene_id:
                self.scenes[index] = scene
                return
        raise ClientNotFoundError("Scene not found")

    def increment_version(self) -> None:
        """Advance the version and record the update time."""
        self.version += 1
        self.updated_at = datetime.now(UTC).isoformat()
