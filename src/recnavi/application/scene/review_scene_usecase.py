# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Review scene use case."""

from recnavi.core.database.base_database import BaseDatabase
from recnavi.core.scene.review_scene import review_scene
from recnavi.core.types.project import Project
from recnavi.core.types.user import User


async def review_scene_usecase(
    *,
    projects_db: BaseDatabase,
    project_id: str,
    scene_id: str,
    result: str,
    review_comment: str | None,
    user: User,
) -> Project:
    """Review a scene recording (approve or reject)."""
    return await review_scene(
        projects_db=projects_db,
        project_id=project_id,
        scene_id=scene_id,
        result=result,
        review_comment=review_comment,
        user=user,
    )
