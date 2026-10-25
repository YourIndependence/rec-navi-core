# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or reproduction of this software is strictly prohibited.
#
# For internal use only.
# developer team.

"""Integration tests for POST /submitProject."""

import os
from typing import cast
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from recnavi.config.variables import FRONTEND_BASE_URL
from recnavi.config.variables import PROJECTS_TABLE_NAME
from recnavi.config.variables import USERS_TABLE_NAME
from recnavi.core.database.base_database import BaseDatabase
from recnavi.core.types.project import Project


def test_submit_project_returns_400_when_no_token(client):
    """Reject missing authentication headers."""
    response = client.post("/submitProject", json={"projectId": "proj-123"})
    assert response.status_code == 400
    assert response.json()["status"] == "error"


@pytest.mark.asyncio
@pytest.mark.skipif(
    os.environ.get("ENV") != "CI",
    reason="needs the in-memory infrastructure injected in CI",
)
async def test_submit_project_notifies_owner(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    """Send the owner an email through the injected notifier."""
    projects_db = cast(
        BaseDatabase,
        client.app.state.database[PROJECTS_TABLE_NAME],
    )
    users_db = cast(
        BaseDatabase,
        client.app.state.database[USERS_TABLE_NAME],
    )
    owner_id = f"it_owner_{uuid4().hex}"
    project = Project(
        project_id=f"it_submit_{uuid4().hex}",
        project_name="Submission",
        group_id="it-group",
        owner_user_id=owner_id,
        # The mock authenticated user is an admin and may act as staff.
        assigned_user_ids=["test-user-123"],
        created_at="2026-01-01T00:00:00Z",
    )
    await projects_db.put_item(project.to_storage_item())
    await users_db.put_item(
        {
            "userId": owner_id,
            "userName": "Owner",
            "email": "owner@example.com",
        },
    )
    notifier = client.app.state.notifier
    notifier.sent.clear()
    try:
        response = client.post(
            "/submitProject",
            headers=auth_headers,
            json={"projectId": project.project_id},
        )
        assert response.status_code == 200, response.text
        assert response.json() == {"status": "ok", "message": None}
        assert len(notifier.sent) == 1
        assert notifier.sent[0]["to_email"] == "owner@example.com"
        assert notifier.sent[0]["review_url"] == (
            f"{FRONTEND_BASE_URL.rstrip('/')}/project/{project.project_id}"
        )
    finally:
        await projects_db.delete_item({"projectId": project.project_id})
        await users_db.delete_item({"userId": owner_id})
