# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""HTTP boundary tests for CMS endpoints."""

from unittest.mock import AsyncMock
from unittest.mock import patch

from fastapi.testclient import TestClient

from recnavi.config.variables import PROJECTS_TABLE_NAME
from recnavi.config.variables import SCENES_TABLE_NAME
from recnavi.config.variables import TEMPLATES_TABLE_NAME
from recnavi.config.variables import USERS_TABLE_NAME
from recnavi.core.types.project import Project
from recnavi.core.types.project import ProjectStatus
from recnavi.core.types.scene import Scene
from recnavi.core.types.scene_master import SceneMaster
from recnavi.core.types.scenes_template import ScenesTemplate
from recnavi.core.types.user import User
from recnavi.core.types.user import UserRole
from tests.mockups.mock_users import get_mock_x_user


def _make_project() -> Project:
    return Project(
        project_id="proj-123",
        project_name="Test Project",
        description="Project description",
        status=ProjectStatus.IN_PROGRESS,
        scenes=[
            Scene(
                scene_id="scene-456",
                scene_principal="cooking",
            ),
        ],
        owner_user_id="test-user-123",
        assigned_user_ids=["staff-456"],
        group_id="it-group",
        created_at="2026-01-01T00:00:00Z",
        updated_at="2026-01-02T00:00:00Z",
        version=3,
    )


def test_get_scene_masters_calls_usecase_and_serializes_response(
    cms_client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    scene_master = SceneMaster(
        scene_principal="cooking",
        title="Cooking",
        thumbnail_uri="s3://bucket/thumbnail.jpg",
        guide_uri="s3://bucket/guide.png",
        max_duration_seconds=60,
    )
    with patch(
        "recnavi.apis.cms.cms_router.get_scene_masters_usecase",
        new=AsyncMock(return_value=[scene_master]),
    ) as usecase:
        response = cms_client.get("/getSceneMasters", headers=auth_headers)

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "scenes": [
            {
                "scenePrincipal": "cooking",
                "title": "Cooking",
                "maxDurationSeconds": 60,
            },
        ],
    }
    usecase.assert_awaited_once_with(
        scenes_db=cms_client.app.state.database[SCENES_TABLE_NAME],
    )


def test_get_templates_calls_usecase_and_excludes_thumbnail_uri(
    cms_client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    template = ScenesTemplate(
        template_id="template-123",
        title="Starter",
        scene_principals=["cooking"],
        thumbnail_uri="s3://bucket/template.jpg",
    )
    with patch(
        "recnavi.apis.cms.cms_router.get_templates_usecase",
        new=AsyncMock(return_value=[template]),
    ) as usecase:
        response = cms_client.get("/getTemplates", headers=auth_headers)

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "templates": [
            {
                "templateId": "template-123",
                "title": "Starter",
                "scenePrincipals": ["cooking"],
            },
        ],
    }
    usecase.assert_awaited_once_with(
        templates_db=cms_client.app.state.database[TEMPLATES_TABLE_NAME],
    )


def test_create_project_parses_request_and_serializes_response(
    cms_client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    project = _make_project()
    with patch(
        "recnavi.apis.cms.cms_router.create_project_usecase",
        new=AsyncMock(return_value=project),
    ) as usecase:
        response = cms_client.post(
            "/createProject",
            headers=auth_headers,
            json={
                "projectName": "Test Project",
                "description": "Project description",
                "scenePrincipals": ["cooking", "walking"],
                "assignedUserIds": ["staff-456"],
            },
        )

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "message": None,
        "project": project.model_dump(by_alias=True, mode="json"),
    }
    usecase.assert_awaited_once_with(
        projects_db=cms_client.app.state.database[PROJECTS_TABLE_NAME],
        project_name="Test Project",
        description="Project description",
        scene_principals=["cooking", "walking"],
        assigned_user_ids=["staff-456"],
        owner=get_mock_x_user(),
    )


def test_update_project_parses_nested_request_and_serializes_response(
    cms_client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    project = _make_project()
    with patch(
        "recnavi.apis.cms.cms_router.update_project_usecase",
        new=AsyncMock(return_value=project),
    ) as usecase:
        response = cms_client.post(
            "/updateProject",
            headers=auth_headers,
            json={
                "project": {
                    "projectId": "proj-123",
                    "projectName": "Test Project",
                    "description": "Project description",
                    "assignedUserIds": ["staff-456"],
                    "scenes": [
                        {
                            "sceneId": "scene-456",
                            "scenePrincipal": "cooking",
                            "assignedUserIds": ["staff-456"],
                        },
                    ],
                    "version": 2,
                },
            },
        )

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "message": None,
        "project": project.model_dump(by_alias=True, mode="json"),
    }
    usecase.assert_awaited_once_with(
        projects_db=cms_client.app.state.database[PROJECTS_TABLE_NAME],
        project_id="proj-123",
        project_name="Test Project",
        description="Project description",
        assigned_user_ids=["staff-456"],
        scenes=[
            Scene(
                scene_id="scene-456",
                scene_principal="cooking",
                assigned_user_ids=["staff-456"],
            ),
        ],
        expected_version=2,
        user=get_mock_x_user(),
        storage=cms_client.app.state.object_storage,
    )


def test_delete_project_parses_request_and_serializes_response(
    cms_client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    with patch(
        "recnavi.apis.cms.cms_router.delete_project_usecase",
        new=AsyncMock(return_value=None),
    ) as usecase:
        response = cms_client.post(
            "/deleteProject",
            headers=auth_headers,
            json={"projectId": "proj-123"},
        )

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "message": None,
        "projectId": "proj-123",
    }
    usecase.assert_awaited_once_with(
        projects_db=cms_client.app.state.database[PROJECTS_TABLE_NAME],
        project_id="proj-123",
        user=get_mock_x_user(),
        storage=cms_client.app.state.object_storage,
    )


def test_get_group_users_uses_authenticated_user_and_exposes_only_member_fields(
    cms_client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    member = User(
        user_id="member",
        user_name="Member",
        role=UserRole.STAFF,
        group_id="it-group",
        email="private@example.com",
        phone_number="123",
        birthday="2000-01-01",
        profile_image_uri="s3://private/avatar.png",
    )
    with patch(
        "recnavi.apis.cms.cms_router.get_group_users_usecase",
        new=AsyncMock(return_value=[member]),
    ) as usecase:
        response = cms_client.get(
            "/getGroupUsers?groupId=other-group",
            headers=auth_headers,
        )
    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "message": None,
        "users": [
            {"userId": "member", "userName": "Member", "role": "staff"},
        ],
    }
    usecase.assert_awaited_once_with(
        users_db=cms_client.app.state.database[USERS_TABLE_NAME],
        user=get_mock_x_user(),
    )
    schema = cms_client.get("/openapi.json").json()
    operation = schema["paths"]["/getGroupUsers"]["get"]
    assert "parameters" not in operation
    assert set(
        schema["components"]["schemas"]["UserSummary"]["properties"],
    ) == {
        "userId",
        "userName",
        "role",
    }
