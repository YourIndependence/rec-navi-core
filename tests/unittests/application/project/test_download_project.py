# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Project download loading and core delegation."""

from unittest.mock import AsyncMock
from unittest.mock import patch

import pytest

from recnavi.application.project.download_project import (
    download_project_usecase,
)
from recnavi.core.types.project import Project
from recnavi.core.types.user import User
from recnavi.core.types.user import UserRole
from recnavi.exceptions.exceptions import ClientNotFoundError
from tests.mockups.mock_database import MockDatabase
from tests.mockups.mock_object_storage import MockObjectStorage


@pytest.mark.asyncio
async def test_download_loads_project_and_delegates():
    value = Project(
        project_id="p",
        project_name="Project",
        owner_user_id="owner",
        group_id="group",
        created_at="2026-10-01T00:00:00Z",
    )
    database = MockDatabase(initial_items=[value.model_dump(by_alias=True)])
    storage = MockObjectStorage(bucket_name="media")
    user = User(
        user_id="owner",
        user_name="Owner",
        role=UserRole.OWNER,
        group_id="group",
    )
    expected_output = value.model_copy(
        update={"download_url": "https://example.org/archive"},
    )
    with patch(
        "recnavi.application.project.download_project.create_project_archive",
        new=AsyncMock(return_value=expected_output),
    ) as core:
        result = await download_project_usecase(
            projects_db=database,
            project_id="p",
            user=user,
            storage=storage,
        )
    assert result is expected_output
    core.assert_awaited_once_with(user=user, project=value, storage=storage)


@pytest.mark.asyncio
async def test_download_unknown_project():
    with pytest.raises(ClientNotFoundError):
        await download_project_usecase(
            projects_db=MockDatabase(),
            project_id="missing",
            user=User(
                user_id="owner",
                user_name="Owner",
                role=UserRole.OWNER,
                group_id="group",
            ),
            storage=MockObjectStorage(bucket_name="media"),
        )
