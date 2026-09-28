# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Project creation domain logic."""

from datetime import UTC
from datetime import datetime
from uuid import uuid4

from recnavi.core.database.base_database import BaseDatabase
from recnavi.core.types.project import Project
from recnavi.core.types.project import ProjectStatus
from recnavi.core.types.scene import Scene
from recnavi.core.types.scene import SceneStatus
from recnavi.core.types.user import User
from recnavi.core.types.user import UserRole
from recnavi.exceptions.exceptions import ClientPermissionError


async def create_project(
    *,
    projects_db: BaseDatabase,
    project_name: str,
    description: str,
    scene_principals: list[str],
    assigned_user_ids: list[str],
    owner: User,
) -> Project:
    """Create a new project with scenes."""
    if owner.role not in [UserRole.OWNER, UserRole.ADMIN]:
        raise ClientPermissionError("Only owners can create projects")

    project_id = str(uuid4())
    now = datetime.now(UTC).isoformat()

    scenes = [
        Scene(
            scene_id=str(uuid4()),
            scene_principal=principal,
            status=SceneStatus.NOT_RECORDED,
            assigned_user_ids=assigned_user_ids,
        )
        for principal in scene_principals
    ]

    project = Project(
        project_id=project_id,
        group_id=owner.group_id,
        project_name=project_name,
        description=description,
        owner_user_id=owner.user_id,
        assigned_user_ids=assigned_user_ids,
        created_at=now,
        updated_at=now,
        status=ProjectStatus.IN_PROGRESS,
        version=0,
        scenes=scenes,
    )

    await projects_db.put_item(project.model_dump(by_alias=True))

    return project
