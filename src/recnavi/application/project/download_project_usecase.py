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
from recnavi.core.storage.base_object_storage import BaseObjectStorage
from recnavi.core.types.project import Project
from recnavi.core.types.user import User


async def download_project_usecase(
    *,
    user: User,
    project: Project,
    bucket_name: str,
    storage: BaseObjectStorage,
) -> str:
    """Download project as zip archive."""
    return await create_project_archive(
        user=user,
        project=project,
        bucket_name=bucket_name,
        storage=storage,
    )
