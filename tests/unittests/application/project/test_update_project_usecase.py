# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or reproduction of this software is strictly prohibited.
#
# For internal use only.
# developer team.

"""Unit tests for update_project_usecase."""

from unittest.mock import AsyncMock
from unittest.mock import patch

import pytest

from recnavi.application.project.update_project_usecase import (
    update_project_usecase,
)
from recnavi.core.types.project import Project
from recnavi.core.types.project import ProjectStatus
from recnavi.core.types.scene_input import SceneInput
from recnavi.core.types.user import User
from recnavi.core.types.user import UserRole
from tests.mockups.mock_database import MockDatabase


@pytest.mark.asyncio
async def test_update_project_usecase_delegates_to_update_project():
    """Test usecase delegates to core update_project collaborator."""
    database = MockDatabase()
    owner = User(
        user_id="owner-1",
        user_name="Owner User",
        group_id="group-1",
        role=UserRole.OWNER,
    )

    expected_project = Project(
        project_id="proj-123",
        group_id="group-1",
        owner_user_id="owner-1",
        project_name="New Name",
        description="New Description",
        assigned_user_ids=["user-1"],
        scenes=[],
        status=ProjectStatus.IN_PROGRESS,
        version=2,
        created_at="2026-01-01T00:00:00Z",
        updated_at="2026-01-01T00:00:00Z",
    )

    scenes = [
        SceneInput(
            scene_principal="cooking",
            assigned_user_ids=["staff-1"],
        ),
    ]

    with patch(
        "recnavi.application.project.update_project_usecase.update_project",
        new=AsyncMock(return_value=expected_project),
    ) as mock_update:
        result = await update_project_usecase(
            projects_db=database,
            project_id="proj-123",
            project_name="New Name",
            description="New Description",
            assigned_user_ids=["user-1"],
            scenes=scenes,
            expected_version=1,
            user=owner,
        )

    mock_update.assert_awaited_once_with(
        projects_db=database,
        project_id="proj-123",
        project_name="New Name",
        description="New Description",
        assigned_user_ids=["user-1"],
        scenes=scenes,
        expected_version=1,
        user=owner,
    )
    assert result is expected_project


@pytest.mark.asyncio
async def test_update_project_usecase_returns_updated_project():
    """Test update_project_usecase returns updated project."""
    database = MockDatabase()
    owner = User(
        user_id="owner-1",
        user_name="Owner User",
        group_id="group-1",
        role=UserRole.OWNER,
    )
    existing_project = Project(
        project_id="proj-123",
        group_id="group-1",
        owner_user_id="owner-1",
        project_name="Old Name",
        description="Old Description",
        assigned_user_ids=[],
        scenes=[],
        status=ProjectStatus.IN_PROGRESS,
        version=1,
        created_at="2026-01-01T00:00:00Z",
        updated_at="2026-01-01T00:00:00Z",
    )
    await database.put_item(existing_project.model_dump(by_alias=True))

    updated_project = await update_project_usecase(
        projects_db=database,
        project_id="proj-123",
        project_name="New Name",
        description="New Description",
        assigned_user_ids=["user-1"],
        scenes=[
            SceneInput(
                scene_principal="cooking",
                assigned_user_ids=["staff-1"],
            ),
        ],
        expected_version=1,
        user=owner,
    )

    assert updated_project.project_id == "proj-123"
    assert updated_project.project_name == "New Name"
    assert updated_project.description == "New Description"
    assert updated_project.assigned_user_ids == ["user-1"]
    assert updated_project.version == 2
    assert len(updated_project.scenes) == 1
    assert updated_project.scenes[0].scene_principal == "cooking"
