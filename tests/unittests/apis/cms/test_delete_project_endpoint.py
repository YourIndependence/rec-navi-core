# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Unit tests for the POST /deleteProject endpoint function."""

from types import SimpleNamespace
from unittest.mock import AsyncMock
from unittest.mock import patch

import pytest

from recnavi.apis.cms.cms_router import delete_project_endpoint
from recnavi.apis.schemas.project_schemas import DeleteProjectRequest
from recnavi.config.variables import PROJECTS_TABLE_NAME
from recnavi.core.types.user import User
from recnavi.core.types.user import UserRole
from tests.mockups.mock_database import MockDatabase
from tests.mockups.mock_object_storage import MockObjectStorage


@pytest.mark.asyncio
async def test_delete_project_endpoint_returns_status_message_project_id():
    """Test the endpoint answers {status, message, projectId}."""
    request = SimpleNamespace(
        app=SimpleNamespace(
            state=SimpleNamespace(
                database={PROJECTS_TABLE_NAME: MockDatabase()},
                object_storage=MockObjectStorage(),
            ),
        ),
    )
    owner = User(
        user_id="owner-1",
        user_name="Owner User",
        group_id="group-456",
        role=UserRole.OWNER,
    )

    with patch(
        "recnavi.application.project.delete_project_usecase.delete_project_usecase",
        new=AsyncMock(return_value="proj-123"),
    ):
        response = await delete_project_endpoint(
            request=request,
            item=DeleteProjectRequest(project_id="proj-123"),
            user=owner,
        )

    assert response.model_dump(by_alias=True, mode="json") == {
        "status": "ok",
        "message": None,
        "projectId": "proj-123",
    }
