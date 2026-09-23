# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Download project use case."""

import base64
import io
import json
import zipfile

from recnavi.core.project.project_download import validate_project_for_download
from recnavi.core.types.project import Project
from recnavi.core.types.user import User
from recnavi.infrastructure.s3.s3_client import download_object
from recnavi.infrastructure.s3.s3_client import generate_presigned_url
from recnavi.infrastructure.s3.s3_client import upload_base64


async def download_project_usecase(
    *,
    user: User,
    project: Project,
    bucket_name: str,
) -> str:
    """Download project as zip archive.

    Args:
        user: Authenticated user.
        project: Project to download.
        bucket_name: S3 bucket name for videos and archives.

    Returns:
        Presigned URL for zip archive download (1-hour expiration).

    Raises:
        ClientAuthorizationError: User is not owner or wrong group.
        ClientUnprocessableEntityError: Project has no scenes or not all approved.

    """
    # Validation
    validate_project_for_download(user=user, project=project)

    # Create in-memory zip archive
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        # Track scene principal counts for unique filenames
        principal_counts: dict[str, int] = {}

        # Build metadata
        metadata = {
            "projectId": project.project_id,
            "projectName": project.project_name,
            "description": project.description,
            "scenes": [],
        }

        # Download videos and add to zip
        for scene in project.scenes:
            # Generate unique filename for duplicate principals
            base_name = scene.scene_principal
            if base_name not in principal_counts:
                principal_counts[base_name] = 1
                filename = f"{base_name}.mp4"
            else:
                principal_counts[base_name] += 1
                filename = f"{base_name}_{principal_counts[base_name]}.mp4"

            # Download video from S3
            video_data = await download_object(
                bucket_name=bucket_name,
                object_key=scene.video_key,
            )

            # Add video to zip
            zf.writestr(filename, video_data)

            # Add scene metadata
            metadata["scenes"].append(
                {
                    "sceneId": scene.scene_id,
                    "scenePrincipal": scene.scene_principal,
                    "fileName": filename,
                },
            )

        # Add metadata.json to zip
        metadata_json = json.dumps(metadata, indent=2, ensure_ascii=False)
        zf.writestr("metadata.json", metadata_json.encode("utf-8"))

    # Get zip bytes
    zip_bytes = zip_buffer.getvalue()

    # Upload zip to S3
    archive_key = f"archives/{project.project_id}.zip"
    base64_data = base64.b64encode(zip_bytes).decode("utf-8")
    await upload_base64(
        bucket_name=bucket_name,
        object_key=archive_key,
        base64_data=base64_data,
        content_type="application/zip",
    )

    # Generate presigned URL (1-hour expiration)
    presigned_url = await generate_presigned_url(
        bucket_name=bucket_name,
        object_key=archive_key,
        expiration=3600,
    )

    return presigned_url
