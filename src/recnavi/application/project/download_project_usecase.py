# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Download project use case."""

import io
import json
import zipfile
from collections.abc import Awaitable
from collections.abc import Callable

from recnavi.core.project.project_download import validate_project_for_download
from recnavi.core.types.project import Project
from recnavi.core.types.user import User


async def download_project_usecase(
    *,
    user: User,
    project: Project,
    bucket_name: str,
    download_object_fn: Callable[[str, str], Awaitable[bytes]],
    generate_presigned_url_fn: Callable[[str, str, int], Awaitable[str]],
    upload_zip_fn: Callable[[str, str, bytes], Awaitable[None]],
) -> str:
    """Download project as zip archive.

    Args:
        user: Authenticated user.
        project: Project to download.
        bucket_name: S3 bucket name for videos and archives.
        download_object_fn: Function to download S3 objects (for dependency injection).
        generate_presigned_url_fn: Function to generate presigned URLs (for dependency injection).
        upload_zip_fn: Function to upload zip to S3 (for dependency injection).

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
            video_data = await download_object_fn(
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
    await upload_zip_fn(
        bucket_name=bucket_name,
        object_key=archive_key,
        zip_bytes=zip_bytes,
    )

    # Generate presigned URL (1-hour expiration)
    presigned_url = await generate_presigned_url_fn(
        bucket_name=bucket_name,
        object_key=archive_key,
        expiration=3600,
    )

    return presigned_url
