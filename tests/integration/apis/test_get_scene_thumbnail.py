# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Staff scene images through the application HTTP boundary."""

import base64
from collections.abc import AsyncIterator
from typing import cast
from uuid import uuid4

import pytest
import pytest_asyncio

from recnavi.config.variables import ENV
from recnavi.config.variables import SCENES_TABLE_NAME
from recnavi.core.database.base_database import BaseDatabase
from recnavi.core.storage.base_object_storage import BaseObjectStorage
from recnavi.main import app


@pytest_asyncio.fixture
async def scene_images() -> AsyncIterator[str]:
    """Seed shared CI infrastructure through public interfaces and clean it up."""
    if ENV != "CI":
        pytest.skip(
            "Staff image success tests use CI in-memory infrastructure",
        )
    database = cast(dict[str, BaseDatabase], app.state.database)[
        SCENES_TABLE_NAME
    ]
    storage = cast(BaseObjectStorage, app.state.object_storage)
    principal = f"it_staff_{uuid4().hex}"
    example_key = f"scenes/{principal}/example.jpg"
    guide_key = f"scenes/{principal}/guide.png"
    try:
        await database.put_item(
            {
                "scenePrincipal": principal,
                "title": "Cooking",
                "thumbnailUri": example_key,
                "guideUri": guide_key,
                "maxDurationSeconds": 60,
            },
        )
        await storage.upload_base64(
            object_key=example_key,
            base64_data=base64.b64encode(b"jpeg-image").decode(),
            content_type="image/jpeg",
        )
        await storage.upload_base64(
            object_key=guide_key,
            base64_data=base64.b64encode(b"png-image").decode(),
            content_type="image/png",
        )
        yield principal
    finally:
        try:
            await database.delete_item({"scenePrincipal": principal})
        finally:
            await storage.delete_objects_by_prefix(
                prefix=f"scenes/{principal}/",
            )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("kind", "body", "mime"),
    [
        ("example", b"jpeg-image", "image/jpeg"),
        ("guide", b"png-image", "image/png"),
    ],
)
async def test_staff_scene_image_bytes(
    client,
    auth_headers,
    scene_images: str,
    kind,
    body,
    mime,
):
    response = client.get(
        "/getSceneThumbnail",
        headers=auth_headers,
        params={"scenePrincipal": scene_images, "kind": kind},
    )
    assert response.status_code == 200
    assert response.content == body
    assert response.headers["content-type"] == mime
    assert response.headers["cache-control"] == "private, max-age=86400"


@pytest.mark.asyncio
async def test_unknown_scene_returns_404(
    client,
    auth_headers,
    scene_images: str,
):
    response = client.get(
        "/getSceneThumbnail",
        headers=auth_headers,
        params={
            "scenePrincipal": f"{scene_images}_unknown",
            "kind": "example",
        },
    )
    assert response.status_code == 404


@pytest.mark.parametrize(
    "params",
    [
        {"scenePrincipal": "public-cooking", "kind": "invalid"},
        {"scenePrincipal": "", "kind": "example"},
        {"scenePrincipal": "public-cooking"},
        {},
    ],
)
def test_invalid_scene_image_query_returns_422(client, auth_headers, params):
    response = client.get(
        "/getSceneThumbnail",
        headers=auth_headers,
        params=params,
    )
    assert response.status_code == 422


def test_scene_image_requires_authentication(client):
    response = client.get(
        "/getSceneThumbnail",
        params={"scenePrincipal": "cooking", "kind": "example"},
    )
    assert response.status_code == 400
    assert response.json()["message"] == "Authorization header is required."
