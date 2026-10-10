# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Build client-facing project views with presigned scene URLs."""

from recnavi.core.database.base_database import BaseDatabase
from recnavi.core.project.create_project import create_project
from recnavi.core.project.project import get_project
from recnavi.core.storage.base_object_storage import BaseObjectStorage
from recnavi.core.types.project import Project
from recnavi.core.types.project_view import ProjectView
from recnavi.core.types.project_view import SceneView
from recnavi.core.types.scene import Scene
from recnavi.core.types.user import User


SCENE_URL_EXPIRATION_SECONDS = 3600


async def attach_scene_urls(
    *,
    storage: BaseObjectStorage,
    bucket_name: str,
    project: Project,
) -> ProjectView:
    """Replace scene storage keys with presigned playback URLs."""
    scenes = [
        await _to_scene_view(
            storage=storage,
            bucket_name=bucket_name,
            scene=scene,
        )
        for scene in project.scenes
    ]
    return ProjectView(
        **project.model_dump(exclude={"scenes"}),
        scenes=scenes,
    )


async def get_project_view(
    *,
    projects_db: BaseDatabase,
    storage: BaseObjectStorage,
    bucket_name: str,
    project_id: str,
    user: User,
) -> ProjectView:
    """Get an accessible project with presigned scene URLs."""
    project = await get_project(
        projects_db=projects_db,
        project_id=project_id,
        user=user,
    )
    return await attach_scene_urls(
        storage=storage,
        bucket_name=bucket_name,
        project=project,
    )


async def create_project_view(
    *,
    projects_db: BaseDatabase,
    storage: BaseObjectStorage,
    bucket_name: str,
    project_name: str,
    description: str,
    scene_principals: list[str],
    assigned_user_ids: list[str],
    owner: User,
) -> ProjectView:
    """Create a project and return it with presigned scene URLs."""
    project = await create_project(
        projects_db=projects_db,
        project_name=project_name,
        description=description,
        scene_principals=scene_principals,
        assigned_user_ids=assigned_user_ids,
        owner=owner,
    )
    return await attach_scene_urls(
        storage=storage,
        bucket_name=bucket_name,
        project=project,
    )


async def _to_scene_view(
    *,
    storage: BaseObjectStorage,
    bucket_name: str,
    scene: Scene,
) -> SceneView:
    video_url = await _presign_or_none(
        storage=storage,
        bucket_name=bucket_name,
        object_key=scene.video_key,
    )
    thumbnail_url = await _presign_or_none(
        storage=storage,
        bucket_name=bucket_name,
        object_key=scene.thumbnail_key,
    )
    return SceneView(
        **scene.model_dump(exclude={"video_key", "thumbnail_key"}),
        video_url=video_url,
        thumbnail_url=thumbnail_url,
    )


async def _presign_or_none(
    *,
    storage: BaseObjectStorage,
    bucket_name: str,
    object_key: str | None,
) -> str | None:
    if object_key is None:
        return None
    return await storage.generate_presigned_url(
        bucket_name=bucket_name,
        object_key=object_key,
        expiration=SCENE_URL_EXPIRATION_SECONDS,
    )
