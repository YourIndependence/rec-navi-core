# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.


"""Project"""

import json
import re
from collections.abc import Sequence
from datetime import UTC
from datetime import datetime
from enum import StrEnum
from typing import Self
from uuid import uuid4

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import alias_generators

from recnavi.core.storage.base_object_storage import BaseObjectStorage
from recnavi.core.types.archive_entry import ArchiveEntry
from recnavi.core.types.scene import Scene
from recnavi.core.types.scene import SceneStatus
from recnavi.core.types.user import User
from recnavi.core.types.user import UserRole
from recnavi.exceptions.exceptions import ClientNotFoundError
from recnavi.exceptions.exceptions import ClientValueError


DOWNLOAD_URL_EXPIRATION_SECONDS = 3600


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

    download_url: str | None = Field(
        default=None,
        description="Presigned URL of the project archive",
    )

    async def create_download_url(self, *, storage: BaseObjectStorage) -> Self:
        """Create a fresh archive and attach its temporary download URL."""
        archive_key = await self._create_download_object(storage=storage)
        self.download_url = await storage.generate_presigned_url(
            object_key=archive_key,
            expiration=DOWNLOAD_URL_EXPIRATION_SECONDS,
        )
        return self

    async def _create_download_object(
        self,
        *,
        storage: BaseObjectStorage,
    ) -> str:
        """Archive approved recordings in shooting order with their metadata."""
        self._validate_download_scenes()
        archive_key = f"projects/{self.project_id}/archives/{uuid4().hex}.zip"
        await storage.create_archive(
            object_key=archive_key,
            entries=self._create_download_entries(),
        )
        return archive_key

    def _validate_download_scenes(self) -> None:
        if not self.scenes or any(
            scene.status != SceneStatus.APPROVED or not scene.video_key
            for scene in self.scenes
        ):
            raise ClientValueError(
                "All project scenes must have approved videos.",
            )
        if any(
            not scene.video_key.startswith(
                f"projects/{self.project_id}/scenes/{scene.scene_id}/",
            )
            or not scene.video_key.endswith(".mp4")
            for scene in self.scenes
            if scene.video_key
        ):
            raise ClientValueError("Scene video must belong to this project.")

    def _create_download_entries(self) -> list[ArchiveEntry]:
        entries: list[ArchiveEntry] = []
        for position, scene in enumerate(self.scenes, start=1):
            principal = (
                re.sub(r"[^\w-]", "_", scene.scene_principal)[:100] or "scene"
            )
            entries.append(
                ArchiveEntry(
                    filename=f"{position:02d}_{principal}.mp4",
                    object_key=scene.video_key,
                ),
            )
        entries.append(self._create_download_metadata_entry(entries=entries))
        return entries

    def _create_download_metadata_entry(
        self,
        *,
        entries: Sequence[ArchiveEntry],
    ) -> ArchiveEntry:
        return ArchiveEntry(
            filename="metadata.json",
            content=json.dumps(
                {
                    "projectId": self.project_id,
                    "projectName": self.project_name,
                    "description": self.description,
                    "scenes": [
                        {
                            "sceneId": scene.scene_id,
                            "scenePrincipal": scene.scene_principal,
                            "createdBy": scene.created_by,
                            "createdAt": scene.created_at,
                            "fileName": entry.filename,
                        }
                        for scene, entry in zip(
                            self.scenes,
                            entries,
                            strict=True,
                        )
                    ],
                },
                ensure_ascii=False,
                indent=2,
            ).encode(),
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

    async def attach_presigned_url(
        self,
        *,
        storage: BaseObjectStorage,
    ) -> Self:
        """Refresh playback URLs on every child scene and return self."""
        self.scenes = [
            await scene.attach_presigned_url(storage=storage)
            for scene in self.scenes
        ]
        return self

    def to_storage_item(self) -> dict[str, object]:
        """Serialize the project and its scenes without temporary URLs."""
        return {
            **self.model_dump(
                by_alias=True,
                exclude={"scenes", "download_url"},
            ),
            "scenes": [scene.to_storage_item() for scene in self.scenes],
        }
