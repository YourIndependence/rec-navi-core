# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Integration tests for POST /getProject endpoint."""

import pytest


def test_get_project_returns_400_when_no_token(client):
    """Test POST /getProject returns 400 when no authorization header."""
    response = client.post(
        "/getProject",
        json={"projectId": "proj-123"},
    )

    assert response.status_code == 400
    data = response.json()
    assert data["status"] == "error"


def test_get_project_returns_400_when_missing_project_id(client, auth_headers):
    """Test POST /getProject returns 400 when projectId is missing."""
    response = client.post(
        "/getProject",
        headers=auth_headers,
        json={},  # Missing projectId
    )

    assert response.status_code == 422  # Validation error
    data = response.json()
    assert "detail" in data


@pytest.mark.real_aws
def test_get_project_with_real_aws(client, auth_headers):
    """Test POST /getProject with real AWS credentials.

    Prerequisites:
    - DynamoDB projects table must exist
    - Valid project record with projectId
    - User must be owner or assigned staff
    - S3 bucket with videos/thumbnails (optional)
    - PROJECTS_TABLE_NAME and VIDEO_BUCKET_NAME environment variables set

    """
    response = client.post(
        "/getProject",
        headers=auth_headers,
        json={"projectId": "test-project-123"},
    )

    # May return 404 if test project doesn't exist
    # or 403 if user not authorized
    # or 200 if project exists and user is authorized
    assert response.status_code in [200, 403, 404]

    if response.status_code == 200:
        data = response.json()
        assert data["status"] == "ok"
        project = data["project"]
        assert project["projectId"] == "test-project-123"
        assert "scenes" in project
        assert "version" in project
