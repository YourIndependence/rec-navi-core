# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or reproduction of this software is strictly prohibited.
#
# For internal use only.
# developer team.

"""Integration tests for GET /getSceneMasters endpoint."""

from collections.abc import AsyncIterator
from contextlib import suppress
from typing import cast
from urllib.parse import urlsplit
from uuid import uuid4

import pytest
import pytest_asyncio

from recnavi.config.variables import MEDIA_BUCKET_NAME
from recnavi.config.variables import SCENES_TABLE_NAME
from recnavi.core.database.base_database import BaseDatabase
from recnavi.main import app


@pytest_asyncio.fixture
async def scene_master_data() -> AsyncIterator[dict[str, object]]:
    """Insert and remove a scene master used by this module."""
    database = cast(
        dict[str, BaseDatabase],
        app.state.database,
    )[SCENES_TABLE_NAME]
    item = {
        "scenePrincipal": f"it_{uuid4()}",
        "title": "Integration Test Scene",
        "thumbnailUri": f"s3://{MEDIA_BUCKET_NAME}/masters/thumbnail.jpg",
        "guideUri": "masters/guide.png",
        "maxDurationSeconds": 5,
    }
    await database.put_item(item)

    try:
        yield item
    finally:
        with suppress(Exception):
            await database.delete_item(
                {"scenePrincipal": item["scenePrincipal"]},
            )


def test_get_scene_masters_returns_401_when_no_token(client):
    """Test GET /getSceneMasters returns 401 when no authorization header."""
    response = client.get("/getSceneMasters")

    assert response.status_code == 401
    data = response.json()
    assert data["status"] == "error"


@pytest.mark.asyncio
async def test_get_scene_masters_returns_injected_scene(
    client,
    auth_headers,
    scene_master_data: dict[str, object],
):
    """Return the scene master injected for this integration test."""
    response = client.get("/getSceneMasters", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    scene = next(
        scene
        for scene in data["scenes"]
        if scene["scenePrincipal"] == scene_master_data["scenePrincipal"]
    )
    assert {
        key: value
        for key, value in scene.items()
        if key not in {"thumbnailUrl", "guideUrl"}
    } == {
        "scenePrincipal": scene_master_data["scenePrincipal"],
        "title": scene_master_data["title"],
        "maxDurationSeconds": scene_master_data["maxDurationSeconds"],
    }
    assert urlsplit(scene["thumbnailUrl"]).path.endswith(
        "/masters/thumbnail.jpg",
    )
    assert urlsplit(scene["guideUrl"]).path.endswith("/masters/guide.png")
    assert response.headers["cache-control"] == "no-store"


@pytest.mark.asyncio
@pytest.mark.parametrize("value", ["", None])
async def test_missing_master_images_return_null(
    client,
    auth_headers,
    scene_master_data,
    value,
):
    database = cast(dict[str, BaseDatabase], app.state.database)[
        SCENES_TABLE_NAME
    ]
    await database.put_item(
        {**scene_master_data, "thumbnailUri": value, "guideUri": value},
    )
    response = client.get("/getSceneMasters", headers=auth_headers)
    assert response.status_code == 200
    scene = next(
        scene
        for scene in response.json()["scenes"]
        if scene["scenePrincipal"] == scene_master_data["scenePrincipal"]
    )
    assert scene["thumbnailUrl"] is None
    assert scene["guideUrl"] is None
