# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Download project use case."""

from recnavi.core.project.project_download import create_project_archive
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
    """Download project as zip archive."""
    return await create_project_archive(
        user=user,
        project=project,
        bucket_name=bucket_name,
        download_video=lambda bn, ok: download_object(
            bucket_name=bn,
            object_key=ok,
        ),
        upload_archive=lambda bn, ok, data: upload_base64(
            bucket_name=bn,
            object_key=ok,
            base64_data=data,
            content_type="application/zip",
        ),
        generate_url=lambda bn, ok: generate_presigned_url(
            bucket_name=bn,
            object_key=ok,
            expiration=3600,
        ),
    )
