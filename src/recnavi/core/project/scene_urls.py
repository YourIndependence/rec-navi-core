# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.
"""Presigned scene URL attachment for client-facing project views."""

from recnavi.core.storage.base_object_storage import BaseObjectStorage
from recnavi.core.types.project import Project


async def attach_scene_urls(
    *,
    storage: BaseObjectStorage,
    project: Project,
) -> Project:
    """Attach playback URLs without mutating the project or its scenes."""
    scenes = [
        await scene.attach_presigned_url(storage=storage)
        for scene in project.scenes
    ]
    return project.model_copy(update={"scenes": scenes}, deep=True)
