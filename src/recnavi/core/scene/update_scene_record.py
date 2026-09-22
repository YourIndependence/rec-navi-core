# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Scene recording update domain logic."""

import uuid

from recnavi.core.database.base_database import BaseDatabase
from recnavi.core.types.project import Project
from recnavi.core.types.user import User
from recnavi.exceptions.exceptions import ClientAuthorizationError
from recnavi.exceptions.exceptions import ClientNotFoundError


async def update_scene_record(
    *,
    projects_db: BaseDatabase,
    project_id: str,
    scene_id: str,
    user: User,
) -> tuple[Project, int, str, str, str | None]:
    """Prepare scene recording update with authorization checks.

    Args:
        projects_db: Database instance for projects table.
        project_id: ID of project containing the scene.
        scene_id: ID of scene to update.
        user: Authenticated user (must be assigned staff).

    Returns:
        Tuple of:
        - Updated project
        - Scene index in scenes array
        - New shot ID (UUID)
        - New video S3 key
        - Old video S3 key (for cleanup, None if first recording)

    Raises:
        ClientNotFoundError: Project or scene not found.
        ClientAuthorizationError: User not in same group or not assigned to scene.

    """
    item = await projects_db.get_item(key={"projectId": project_id})
    if not item:
        raise ClientNotFoundError("Project not found")

    project = Project.model_validate(item)

    if project.group_id != user.group_id:
        raise ClientAuthorizationError(
            "Access to other group's project is forbidden",
        )

    scene_index = None
    scene = None
    for i, s in enumerate(project.scenes):
        if s.scene_id == scene_id:
            scene_index = i
            scene = s
            break

    if scene is None:
        raise ClientNotFoundError("Scene not found")

    if user.user_id not in scene.assigned_user_ids:
        raise ClientAuthorizationError("Not assigned to this scene")

    shot_id = str(uuid.uuid4())
    new_video_key = f"projects/{project_id}/scenes/{scene_id}/{shot_id}.mp4"
    old_video_key = scene.video_key

    return project, scene_index, shot_id, new_video_key, old_video_key
