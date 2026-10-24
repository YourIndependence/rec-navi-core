# Copyright (c) 2026 YourIndependence. All rights reserved.

"""Project reads attach URLs after core authorization and filtering."""

from unittest.mock import AsyncMock
from unittest.mock import patch

import pytest

from recnavi.application.project.get_project import get_project_usecase
from recnavi.core.types.project import Project
from recnavi.core.types.scene import Scene
from recnavi.core.types.user import User
from recnavi.core.types.user import UserRole
from tests.mockups.mock_database import MockDatabase
from tests.mockups.mock_object_storage import MockObjectStorage


@pytest.mark.asyncio
async def test_get_project_returns_playback_urls_without_changing_database():
    project = Project(
        project_id="project",
        project_name="Project",
        group_id="group",
        owner_user_id="owner",
        created_at="2026-01-01T00:00:00Z",
        scenes=[
            Scene(
                scene_id="scene",
                scene_principal="opening",
                video_key="recording.mp4",
                thumbnail_key="thumbnail.jpg",
            ),
        ],
    )
    item = project.to_storage_item()
    database = MockDatabase([item])
    storage = MockObjectStorage(bucket_name="media")
    result = await get_project_usecase(
        projects_db=database,
        storage=storage,
        project_id="project",
        user=User(
            user_id="owner",
            user_name="Owner",
            group_id="group",
            role=UserRole.OWNER,
        ),
    )
    assert (
        result.scenes[0].video_url == "mock://media/recording.mp4?expires=3600"
    )
    assert (
        result.scenes[0].thumbnail_url
        == "mock://media/thumbnail.jpg?expires=3600"
    )
    assert result.to_storage_item() == item
    assert database.items == [item]
    assert "videoKey" not in result.model_dump(by_alias=True)["scenes"][0]


@pytest.mark.asyncio
async def test_get_project_orchestrates_authorized_read_and_url_attachment():
    database = MockDatabase()
    storage = MockObjectStorage(bucket_name="media")
    expected_output = AsyncMock(spec=Project)
    expected_output.attach_presigned_url.return_value = expected_output
    user = User(
        user_id="owner",
        user_name="Owner",
        group_id="group",
        role=UserRole.OWNER,
    )
    with (
        patch(
            "recnavi.application.project.get_project.get_project",
            new=AsyncMock(return_value=expected_output),
        ) as get_project,
    ):
        result = await get_project_usecase(
            projects_db=database,
            storage=storage,
            project_id="project",
            user=user,
        )
    get_project.assert_awaited_once_with(
        projects_db=database,
        project_id="project",
        user=user,
    )
    expected_output.attach_presigned_url.assert_awaited_once_with(
        storage=storage,
    )
    assert result is expected_output
