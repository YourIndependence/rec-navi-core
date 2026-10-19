# Copyright (c) 2026 YourIndependence. All rights reserved.

"""Project reads attach URLs after core authorization and filtering."""

from unittest.mock import AsyncMock
from unittest.mock import patch

import pytest

from recnavi.application.project.get_projects import get_projects_usecase
from recnavi.core.types.project import Project
from recnavi.core.types.scene import Scene
from tests.mockups.mock_database import MockDatabase
from tests.mockups.mock_object_storage import MockObjectStorage


@pytest.mark.asyncio
async def test_get_projects_returns_playback_urls_without_changing_database():
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
    projects, cursor = await get_projects_usecase(
        projects_db=database,
        storage=storage,
        user_id="owner",
        group_id="group",
        cursor=None,
    )
    assert cursor is None
    result = projects[0]
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
async def test_get_projects_preserves_filtered_results_and_cursor():
    database = MockDatabase()
    storage = MockObjectStorage(bucket_name="media")
    project = object()
    expected_output = ([project], "next-page")
    with (
        patch(
            "recnavi.application.project.get_projects.get_projects",
            new=AsyncMock(return_value=expected_output),
        ) as get_projects,
        patch(
            "recnavi.application.project.get_projects.attach_scene_urls",
            new=AsyncMock(return_value=project),
        ) as attach_urls,
    ):
        result = await get_projects_usecase(
            projects_db=database,
            storage=storage,
            user_id="owner",
            group_id="group",
            limit=12,
            cursor="previous-page",
        )
    get_projects.assert_awaited_once_with(
        projects_db=database,
        user_id="owner",
        group_id="group",
        limit=12,
        cursor="previous-page",
    )
    attach_urls.assert_awaited_once_with(storage=storage, project=project)
    assert result == expected_output
