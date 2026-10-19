# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Download an approved project as an archive."""

from recnavi.core.database.base_database import BaseDatabase
from recnavi.core.project.download_project import create_project_archive
from recnavi.core.storage.base_object_storage import BaseObjectStorage
from recnavi.core.types.project import Project
from recnavi.core.types.project_archive import ProjectArchive
from recnavi.core.types.user import User
from recnavi.exceptions.exceptions import ClientNotFoundError


async def download_project_usecase(
    *,
    projects_db: BaseDatabase,
    project_id: str,
    user: User,
    storage: BaseObjectStorage,
) -> ProjectArchive:
    """Load project state and apply archive access and eligibility policy."""
    item = await projects_db.get_item(key={"projectId": project_id})
    if item is None:
        raise ClientNotFoundError("Project not found")
    return await create_project_archive(
        user=user,
        project=Project.model_validate(item),
        storage=storage,
    )
