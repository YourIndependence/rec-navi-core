# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Create project use case."""

from recnavi.core.database.base_database import BaseDatabase
from recnavi.core.project.create_project import create_project
from recnavi.core.types.project import Project
from recnavi.core.types.user import User


async def create_project_usecase(
    *,
    projects_db: BaseDatabase,
    project_name: str,
    description: str,
    scene_principals: list[str],
    assigned_user_ids: list[str],
    owner: User,
) -> Project:
    """Create a new project and save to database."""
    project = create_project(
        project_name=project_name,
        description=description,
        scene_principals=scene_principals,
        assigned_user_ids=assigned_user_ids,
        owner=owner,
    )

    await projects_db.put_item(project.model_dump(by_alias=True))

    return project
