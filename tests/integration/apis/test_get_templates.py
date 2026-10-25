# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or reproduction of this software is strictly prohibited.
#
# For internal use only.
# developer team.

"""Integration tests for GET /getTemplates endpoint."""

from collections.abc import AsyncIterator
from contextlib import suppress
from typing import cast
from urllib.parse import urlsplit
from uuid import uuid4

import pytest
import pytest_asyncio

from recnavi.config.variables import MEDIA_BUCKET_NAME
from recnavi.config.variables import TEMPLATES_TABLE_NAME
from recnavi.core.database.base_database import BaseDatabase
from recnavi.main import app


@pytest_asyncio.fixture
async def template_data() -> AsyncIterator[dict[str, object]]:
    """Insert and remove a template used by this module."""
    database = cast(
        dict[str, BaseDatabase],
        app.state.database,
    )[TEMPLATES_TABLE_NAME]
    item = {
        "templateId": f"it_{uuid4()}",
        "title": "Integration Test Template",
        "scenePrincipals": ["it_scene_master"],
        "thumbnailUri": f"s3://{MEDIA_BUCKET_NAME}/templates/template.jpg",
    }
    await database.put_item(item)

    try:
        yield item
    finally:
        with suppress(Exception):
            await database.delete_item(
                {"templateId": item["templateId"]},
            )


def test_get_templates_returns_401_when_no_token(client):
    """Test GET /getTemplates returns 401 when no authorization header."""
    response = client.get("/getTemplates")

    assert response.status_code == 401
    data = response.json()
    assert data["status"] == "error"


@pytest.mark.asyncio
async def test_get_templates_returns_injected_template(
    client,
    auth_headers,
    template_data: dict[str, object],
):
    """Return the template injected for this integration test."""
    response = client.get("/getTemplates", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    template = next(
        template
        for template in data["templates"]
        if template["templateId"] == template_data["templateId"]
    )
    assert {
        key: value for key, value in template.items() if key != "thumbnailUrl"
    } == {
        "templateId": template_data["templateId"],
        "title": template_data["title"],
        "scenePrincipals": template_data["scenePrincipals"],
    }
    assert urlsplit(template["thumbnailUrl"]).path.endswith(
        "/templates/template.jpg",
    )
    assert response.headers["cache-control"] == "no-store"


@pytest.mark.asyncio
@pytest.mark.parametrize("value", ["", None])
async def test_missing_template_image_returns_null(
    client,
    auth_headers,
    template_data,
    value,
):
    database = cast(dict[str, BaseDatabase], app.state.database)[
        TEMPLATES_TABLE_NAME
    ]
    await database.put_item({**template_data, "thumbnailUri": value})
    response = client.get("/getTemplates", headers=auth_headers)
    assert response.status_code == 200
    template = next(
        template
        for template in response.json()["templates"]
        if template["templateId"] == template_data["templateId"]
    )
    assert template["thumbnailUrl"] is None
