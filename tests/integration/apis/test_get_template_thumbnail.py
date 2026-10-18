# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Public template images through the full application HTTP boundary."""

import base64
from collections.abc import AsyncIterator
from typing import cast
from uuid import uuid4

import pytest
import pytest_asyncio

from recnavi.config.variables import ENV
from recnavi.config.variables import TEMPLATES_TABLE_NAME
from recnavi.core.database.base_database import BaseDatabase
from recnavi.core.storage.base_object_storage import BaseObjectStorage
from recnavi.main import app


@pytest_asyncio.fixture
async def template_images() -> AsyncIterator[str]:
    """Seed shared CI infrastructure and always remove generated data."""
    if ENV != "CI":
        pytest.skip(
            "Template image success tests use CI in-memory infrastructure",
        )
    database = cast(dict[str, BaseDatabase], app.state.database)[
        TEMPLATES_TABLE_NAME
    ]
    storage = cast(BaseObjectStorage, app.state.scene_images_storage)
    template_id = f"it_thumbnail_{uuid4().hex}"
    prefix = f"templates/{template_id}/"
    try:
        for suffix, mime in [("jpg", "image/jpeg"), ("png", "image/png")]:
            key = f"{prefix}thumbnail.{suffix}"
            await database.put_item(
                {
                    "templateId": f"{template_id}_{suffix}",
                    "title": "Cafe",
                    "thumbnailUri": key,
                },
            )
            await storage.upload_base64(
                object_key=key,
                base64_data=base64.b64encode(
                    b"image-" + suffix.encode(),
                ).decode(),
                content_type=mime,
            )
        await database.put_item(
            {
                "templateId": f"{template_id}_empty",
                "title": "No image",
                "thumbnailUri": "",
            },
        )
        yield template_id
    finally:
        try:
            for suffix in ["jpg", "png", "empty"]:
                await database.delete_item(
                    {"templateId": f"{template_id}_{suffix}"},
                )
        finally:
            await storage.delete_objects_by_prefix(prefix=prefix)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("suffix", "mime"),
    [("jpg", "image/jpeg"), ("png", "image/png")],
)
async def test_public_template_image_bytes(
    client,
    template_images: str,
    suffix,
    mime,
):
    response = client.get(
        "/getTemplateThumbnail",
        params={"templateId": f"{template_images}_{suffix}"},
    )
    assert response.status_code == 200
    assert response.content == b"image-" + suffix.encode()
    assert response.headers["content-type"] == mime
    assert response.headers["cache-control"] == "public, max-age=86400"


@pytest.mark.asyncio
@pytest.mark.parametrize("suffix", ["unknown", "empty"])
async def test_template_thumbnail_not_found(
    client,
    template_images: str,
    suffix,
):
    response = client.get(
        "/getTemplateThumbnail",
        params={"templateId": f"{template_images}_{suffix}"},
    )
    assert response.status_code == 404


@pytest.mark.parametrize("params", [{}, {"templateId": ""}])
def test_invalid_template_thumbnail_query(client, params):
    response = client.get("/getTemplateThumbnail", params=params)
    assert response.status_code == 422
