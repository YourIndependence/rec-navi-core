# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Project download validation logic."""

import base64
import io
import json
import zipfile

from recnavi.core.storage.base_object_storage import BaseObjectStorage
from recnavi.core.types.project import Project
from recnavi.core.types.scene import SceneStatus
from recnavi.core.types.user import User
from recnavi.core.types.user import UserRole
from recnavi.exceptions.exceptions import ClientAuthorizationError
from recnavi.exceptions.exceptions import ClientUnprocessableEntityError


def validate_project_for_download(
    *,
    user: User,
    project: Project,
) -> None:
    """Validate project download eligibility."""
    if user.role != UserRole.OWNER:
        raise ClientAuthorizationError("forbidden")

    if user.group_id != project.group_id:
        raise ClientAuthorizationError("forbidden")

    if not project.scenes:
        raise ClientUnprocessableEntityError(
            "Project has no scenes. Cannot create archive.",
        )

    unapproved_scenes = [
        scene
        for scene in project.scenes
        if scene.status != SceneStatus.APPROVE
    ]
    if unapproved_scenes:
        unapproved_ids = [scene.scene_id for scene in unapproved_scenes]
        raise ClientUnprocessableEntityError(
            f"Not all scenes are approved. Unapproved scenes: {unapproved_ids}",
        )


async def create_project_archive(
    *,
    user: User,
    project: Project,
    bucket_name: str,
    storage: BaseObjectStorage,
) -> str:
    """Build a zip archive of approved scene videos and return its download URL."""
    validate_project_for_download(user=user, project=project)

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        principal_counts: dict[str, int] = {}

        metadata = {
            "projectId": project.project_id,
            "projectName": project.project_name,
            "description": project.description,
            "scenes": [],
        }

        for scene in project.scenes:
            base_name = scene.scene_principal
            if base_name not in principal_counts:
                principal_counts[base_name] = 1
                filename = f"{base_name}.mp4"
            else:
                principal_counts[base_name] += 1
                filename = f"{base_name}_{principal_counts[base_name]}.mp4"

            video_data = await storage.download_object(
                bucket_name=bucket_name,
                object_key=scene.video_key,
            )
            zf.writestr(filename, video_data)

            metadata["scenes"].append(
                {
                    "sceneId": scene.scene_id,
                    "scenePrincipal": scene.scene_principal,
                    "fileName": filename,
                },
            )

        metadata_json = json.dumps(metadata, indent=2, ensure_ascii=False)
        zf.writestr("metadata.json", metadata_json.encode("utf-8"))

    archive_key = f"archives/{project.project_id}.zip"
    base64_data = base64.b64encode(zip_buffer.getvalue()).decode("utf-8")
    await storage.upload_base64(
        bucket_name=bucket_name,
        object_key=archive_key,
        base64_data=base64_data,
        content_type="application/zip",
    )

    return await storage.generate_presigned_url(
        bucket_name=bucket_name,
        object_key=archive_key,
        expiration=3600,
    )
