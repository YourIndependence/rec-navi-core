# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Approved-project archive policy and naming."""

import json
import re
from uuid import uuid4

from recnavi.core.storage.base_object_storage import BaseObjectStorage
from recnavi.core.types.archive_entry import ArchiveEntry
from recnavi.core.types.project import Project
from recnavi.core.types.project_archive import ProjectArchive
from recnavi.core.types.scene import SceneStatus
from recnavi.core.types.user import User
from recnavi.core.types.user import UserRole
from recnavi.exceptions.exceptions import ClientAuthorizationError
from recnavi.exceptions.exceptions import ClientValueError


DOWNLOAD_URL_EXPIRATION_SECONDS = 3600


def validate_project_for_download(*, user: User, project: Project) -> None:
    """Require the same-group owner and a complete approved recording set."""
    if (
        user.role != UserRole.OWNER
        or user.group_id != project.group_id
        or user.user_id != project.owner_user_id
    ):
        raise ClientAuthorizationError(
            "Only the project owner can download it.",
        )
    if not project.scenes or any(
        scene.status != SceneStatus.APPROVED or not scene.video_key
        for scene in project.scenes
    ):
        raise ClientValueError("All project scenes must have approved videos.")
    if any(
        not scene.video_key.startswith(
            f"projects/{project.project_id}/scenes/{scene.scene_id}/",
        )
        or not scene.video_key.endswith(".mp4")
        for scene in project.scenes
        if scene.video_key
    ):
        raise ClientValueError("Scene video must belong to this project.")


async def create_project_archive(
    *,
    user: User,
    project: Project,
    storage: BaseObjectStorage,
) -> ProjectArchive:
    """Archive scenes in project shooting order with recording metadata."""
    validate_project_for_download(user=user, project=project)
    entries: list[ArchiveEntry] = []
    scene_metadata: list[dict[str, str | None]] = []
    for position, scene in enumerate(project.scenes, start=1):
        principal = (
            re.sub(r"[^\w-]", "_", scene.scene_principal)[:100] or "scene"
        )
        filename = f"{position:02d}_{principal}.mp4"
        entries.append(
            ArchiveEntry(filename=filename, object_key=scene.video_key),
        )
        scene_metadata.append(
            {
                "sceneId": scene.scene_id,
                "scenePrincipal": scene.scene_principal,
                "createdBy": scene.created_by,
                "createdAt": scene.created_at,
                "fileName": filename,
            },
        )
    metadata = {
        "projectId": project.project_id,
        "projectName": project.project_name,
        "description": project.description,
        "scenes": scene_metadata,
    }
    entries.append(
        ArchiveEntry(
            filename="metadata.json",
            content=json.dumps(
                metadata,
                ensure_ascii=False,
                indent=2,
            ).encode(),
        ),
    )
    archive_key = f"projects/{project.project_id}/archives/{uuid4().hex}.zip"
    await storage.create_archive(object_key=archive_key, entries=entries)
    download_url = await storage.generate_presigned_url(
        object_key=archive_key,
        expiration=DOWNLOAD_URL_EXPIRATION_SECONDS,
    )
    return ProjectArchive(
        download_url=download_url,
        expires_in_seconds=DOWNLOAD_URL_EXPIRATION_SECONDS,
    )
