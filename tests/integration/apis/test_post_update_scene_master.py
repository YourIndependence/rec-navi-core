# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or reproduction of this software is strictly prohibited.
#
# For internal use only.
# developer team.

"""Integration tests for POST /updateSceneMaster endpoint."""

from uuid import uuid4

import pytest

from recnavi.apis.auth.auth import verify_user
from recnavi.config.variables import ENV
from recnavi.config.variables import MEDIA_BUCKET_NAME
from recnavi.config.variables import SCENES_TABLE_NAME
from recnavi.core.storage.image_urls import MEDIA_URL_EXPIRATION_SECONDS
from recnavi.core.types.user import UserRole
from recnavi.main import app
from tests.mockups.mock_users import get_mock_x_user


def test_update_scene_master_returns_400_when_no_token(client):
    """Test POST /updateSceneMaster returns 400 when no authorization header."""
    response = client.post(
        "/updateSceneMaster",
        json={
            "scenePrincipal": "it_invalid",
            "title": "Cooking Scene",
            "maxDurationSeconds": 5,
            "exampleImage": "ZmFrZSBpbWFnZQ==",
            "guideImage": "ZmFrZSBndWlkZQ==",
        },
    )
    assert response.status_code == 400
    data = response.json()
    assert data["status"] == "error"


def test_update_scene_master_returns_422_for_wrapped_payload(
    client,
    auth_headers,
):
    """Test POST /updateSceneMaster rejects the old wrapped payload shape."""
    response = client.post(
        "/updateSceneMaster",
        headers=auth_headers,
        json={
            "sceneMaster": {
                "scenePrincipal": "cooking",
                "title": "Cooking Scene",
                "maxDurationSeconds": 5,
            },
        },
    )
    assert response.status_code == 422


@pytest.mark.asyncio
@pytest.mark.skipif(ENV != "CI", reason="Requires CI in-memory infrastructure")
async def test_update_scene_master_returns_updated_scene_master(
    client,
    auth_headers,
):
    """Verify the master API accepts and returns explicit master fields."""
    principal = f"it_master_{uuid4().hex}"
    database = app.state.database[SCENES_TABLE_NAME]
    storage = app.state.object_storage
    try:
        response = client.post(
            "/updateSceneMaster",
            headers=auth_headers,
            json={
                "scenePrincipal": principal,
                "title": "Cooking Master",
                "maxDurationSeconds": 5,
                "exampleImage": "ZXhhbXBsZQ==",
                "guideImage": "Z3VpZGU=",
            },
        )
        assert response.status_code == 200, response.text
        data = response.json()
        assert "scenes" not in data
        assert "sceneMasters" not in data
        master = data["sceneMaster"]
        assert master["scenePrincipal"] == principal
        assert master["title"] == "Cooking Master"
        assert master["maxDurationSeconds"] == 5
        assert "thumbnailUri" not in master
        assert "guideUri" not in master
        for field in ("thumbnailUrl", "guideUrl"):
            assert master[field].startswith(
                f"mock://{MEDIA_BUCKET_NAME}/scenes/{principal}/",
            )
            assert master[field].endswith(
                f"?expires={MEDIA_URL_EXPIRATION_SECONDS}",
            )
        stored = await database.get_item({"scenePrincipal": principal})
        assert stored["title"] == "Cooking Master"
        assert "thumbnailUrl" not in stored
        assert "guideUrl" not in stored
        response = client.post(
            "/updateSceneMaster",
            headers=auth_headers,
            json={
                "scenePrincipal": principal,
                "title": "Updated Master",
                "maxDurationSeconds": 7,
            },
        )
        assert response.status_code == 200, response.text
        updated_master = response.json()["sceneMaster"]
        assert updated_master["title"] == "Updated Master"
        assert updated_master["maxDurationSeconds"] == 7
        assert updated_master["thumbnailUrl"] == master["thumbnailUrl"]
        assert updated_master["guideUrl"] == master["guideUrl"]
        response = client.post(
            "/updateSceneMaster",
            headers=auth_headers,
            json={"scenePrincipal": principal, "maxDurationSeconds": 8},
        )
        assert response.status_code == 200, response.text
        partial = response.json()["sceneMaster"]
        assert partial["title"] == "Updated Master"
        assert partial["maxDurationSeconds"] == 8
        response = client.post(
            "/updateSceneMaster",
            headers=auth_headers,
            json={"scenePrincipal": principal, "exampleImage": "bmV3"},
        )
        assert response.status_code == 200, response.text
        image_only = response.json()["sceneMaster"]
        assert image_only["title"] == partial["title"]
        assert (
            image_only["maxDurationSeconds"] == partial["maxDurationSeconds"]
        )
        assert image_only["thumbnailUrl"] != partial["thumbnailUrl"]
        assert image_only["guideUrl"] == partial["guideUrl"]
        stored = await database.get_item({"scenePrincipal": principal})
        assert stored["thumbnailUri"].startswith(f"scenes/{principal}/")
    finally:
        await storage.delete_objects_by_prefix(prefix=f"scenes/{principal}/")
        await database.delete_item(key={"scenePrincipal": principal})


@pytest.mark.parametrize("duration", [0, 11])
def test_update_scene_master_rejects_duration_outside_bounds(
    client,
    auth_headers,
    duration,
):
    """Reject invalid recording durations at the HTTP boundary."""
    response = client.post(
        "/updateSceneMaster",
        headers=auth_headers,
        json={
            "scenePrincipal": "it_invalid",
            "title": "Invalid Duration",
            "maxDurationSeconds": duration,
            "exampleImage": "ZXhhbXBsZQ==",
            "guideImage": "Z3VpZGU=",
        },
    )
    assert response.status_code == 422


@pytest.mark.parametrize("role", [UserRole.OWNER, UserRole.STAFF])
def test_update_scene_master_forbids_non_admin(client, auth_headers, role):
    previous = app.dependency_overrides[verify_user]
    app.dependency_overrides[verify_user] = lambda: (
        get_mock_x_user().model_copy(update={"role": role})
    )
    try:
        response = client.post(
            "/updateSceneMaster",
            headers=auth_headers,
            json={
                "scenePrincipal": "it_denied",
                "title": "Denied",
                "maxDurationSeconds": 5,
                "exampleImage": "ZXhhbXBsZQ==",
                "guideImage": "Z3VpZGU=",
            },
        )
        assert response.status_code == 403
        assert response.json()["status"] == "error"
    finally:
        app.dependency_overrides[verify_user] = previous


@pytest.mark.parametrize("principal", [None, "", "../other", "nested/key"])
def test_update_scene_master_requires_readable_client_key(
    client,
    auth_headers,
    principal,
):
    response = client.post(
        "/updateSceneMaster",
        headers=auth_headers,
        json={
            "scenePrincipal": principal,
            "title": "Invalid",
            "maxDurationSeconds": 5,
            "exampleImage": "ZXhhbXBsZQ==",
            "guideImage": "Z3VpZGU=",
        },
    )
    assert response.status_code == 422


def test_update_scene_master_validates_all_images_before_upload(
    client,
    auth_headers,
):
    response = client.post(
        "/updateSceneMaster",
        headers=auth_headers,
        json={
            "scenePrincipal": "it_invalid_image",
            "title": "Invalid",
            "maxDurationSeconds": 5,
            "exampleImage": "ZXhhbXBsZQ==",
            "guideImage": "!invalid!",
        },
    )
    assert response.status_code == 422


def test_update_scene_master_rejects_creation_without_images(
    client,
    auth_headers,
):
    response = client.post(
        "/updateSceneMaster",
        headers=auth_headers,
        json={
            "scenePrincipal": "it_missing_images",
            "title": "Missing images",
            "maxDurationSeconds": 5,
        },
    )
    assert response.status_code == 400
    assert response.json()["message"] == (
        "exampleImage and guideImage are required when creating a new scene"
    )


@pytest.mark.parametrize("missing_field", ["title", "maxDurationSeconds"])
def test_update_scene_master_requires_metadata_on_create(
    client,
    auth_headers,
    missing_field,
):
    payload = {
        "scenePrincipal": "it_missing_metadata",
        "title": "New",
        "maxDurationSeconds": 5,
        "exampleImage": "ZXhhbXBsZQ==",
        "guideImage": "Z3VpZGU=",
    }
    payload.pop(missing_field)
    response = client.post(
        "/updateSceneMaster",
        headers=auth_headers,
        json=payload,
    )
    assert response.status_code == 400
