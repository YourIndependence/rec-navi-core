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

from recnavi.config.variables import ENV
from recnavi.config.variables import SCENES_TABLE_NAME
from recnavi.main import app


def test_update_scene_master_returns_400_when_no_token(client):
    """Test POST /updateSceneMaster returns 400 when no authorization header."""
    response = client.post(
        "/updateSceneMaster",
        json={
            "scenePrincipal": None,
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
async def test_update_scene_master_returns_scene_masters(client, auth_headers):
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
        master = next(
            item
            for item in data["sceneMasters"]
            if item["scenePrincipal"] == principal
        )
        assert master["title"] == "Cooking Master"
        assert master["maxDurationSeconds"] == 5
        assert "thumbnailUri" not in master
        assert "guideUri" not in master
        stored = await database.get_item({"scenePrincipal": principal})
        assert stored["title"] == "Cooking Master"
    finally:
        await storage.delete_objects_by_prefix(prefix=f"scenes/{principal}/")
        await database.delete_item(key={"scenePrincipal": principal})
