# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or reproduction of this software is strictly prohibited.
#
# For internal use only.
# developer team.

"""Template HTTP integration with real application and domain collaborators."""

from uuid import uuid4

import pytest

from recnavi.apis.auth.auth import verify_user
from recnavi.config.variables import TEMPLATES_TABLE_NAME
from recnavi.core.types.user import UserRole
from recnavi.main import app
from tests.mockups.mock_users import get_mock_x_user


@pytest.mark.asyncio
async def test_update_template_create_edit_and_read(client, auth_headers):
    key = f"it_template_{uuid4().hex}"
    database = app.state.database[TEMPLATES_TABLE_NAME]
    storage = app.state.object_storage
    try:
        response = client.post(
            "/updateTemplate",
            headers=auth_headers,
            json={
                "templateId": key,
                "title": "Starter",
                "scenePrincipals": [],
                "thumbnailImage": "b2xk",
            },
        )
        assert response.status_code == 200, response.text
        template = response.json()["template"]
        assert template["thumbnailUrl"]
        assert "thumbnailUri" not in template
        response = client.post(
            "/updateTemplate",
            headers=auth_headers,
            json={"templateId": key, "title": "Renamed"},
        )
        assert response.status_code == 200, response.text
        assert (
            response.json()["template"]["thumbnailUrl"]
            == template["thumbnailUrl"]
        )
        response = client.post(
            "/updateTemplate",
            headers=auth_headers,
            json={"templateId": key, "thumbnailImage": "bmV3"},
        )
        assert response.status_code == 200, response.text
        assert (
            response.json()["template"]["thumbnailUrl"]
            != template["thumbnailUrl"]
        )
        stored = await database.get_item({"templateId": key})
        assert stored["thumbnailUri"].startswith(f"templates/{key}/")
        assert "thumbnailUrl" not in stored
        response = client.get("/getTemplates", headers=auth_headers)
        assert response.status_code == 200, response.text
        assert any(
            item["templateId"] == key and item["title"] == "Renamed"
            for item in response.json()["templates"]
        )
    finally:
        await database.delete_item(key={"templateId": key})
        await storage.delete_objects_by_prefix(prefix=f"templates/{key}/")


@pytest.mark.parametrize("role", [UserRole.OWNER, UserRole.STAFF])
def test_update_template_forbids_non_admin(client, auth_headers, role):
    previous = app.dependency_overrides[verify_user]
    app.dependency_overrides[verify_user] = lambda: (
        get_mock_x_user().model_copy(update={"role": role})
    )
    try:
        response = client.post(
            "/updateTemplate",
            headers=auth_headers,
            json={"templateId": "it_denied"},
        )
        assert response.status_code == 403
    finally:
        app.dependency_overrides[verify_user] = previous


@pytest.mark.parametrize(
    "payload",
    [
        {"templateId": "../unsafe"},
        {"templateId": None},
        {},
        {"templateId": "it_invalid", "thumbnailImage": "!invalid!"},
        {"templateId": "it_invalid", "thumbnailImage": ""},
        {"template": {"templateId": "it_nested"}},
    ],
)
def test_update_template_rejects_invalid_payload(
    client,
    auth_headers,
    payload,
):
    response = client.post(
        "/updateTemplate",
        headers=auth_headers,
        json=payload,
    )
    assert response.status_code == 422


def test_update_template_requires_image_on_create(client, auth_headers):
    response = client.post(
        "/updateTemplate",
        headers=auth_headers,
        json={
            "templateId": "it_missing_image",
            "title": "Missing",
            "scenePrincipals": [],
        },
    )
    assert response.status_code == 400


def test_update_template_without_auth(client):
    response = client.post(
        "/updateTemplate",
        json={"templateId": "it_unauthorized"},
    )
    assert response.status_code == 400


def test_update_template_rejects_unknown_scene(client, auth_headers):
    response = client.post(
        "/updateTemplate",
        headers=auth_headers,
        json={
            "templateId": "it_unknown",
            "title": "Unknown",
            "scenePrincipals": ["it_nonexistent"],
            "thumbnailImage": "bmV3",
        },
    )
    assert response.status_code == 400
