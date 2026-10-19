# Copyright (c) 2026 YourIndependence. All rights reserved.

"""Template listing orchestration."""

from unittest.mock import AsyncMock
from unittest.mock import patch

import pytest

from recnavi.application.scene.get_templates import get_templates_usecase
from recnavi.core.types.scenes_template import ScenesTemplate
from tests.mockups.mock_database import MockDatabase
from tests.mockups.mock_object_storage import MockObjectStorage


@pytest.mark.asyncio
async def test_get_templates_attaches_urls_and_returns_core_views():
    database = MockDatabase()
    storage = MockObjectStorage(bucket_name="media")
    templates = [ScenesTemplate(template_id="cafe", title="Cafe")]
    expected_output = [
        ScenesTemplate(
            template_id="cafe",
            title="Cafe",
            thumbnail_url="https://signed/image",
        ),
    ]
    with (
        patch(
            "recnavi.application.scene.get_templates.get_templates",
            new=AsyncMock(return_value=templates),
        ) as get_metadata,
        patch(
            "recnavi.application.scene.get_templates.attach_template_urls",
            new=AsyncMock(return_value=expected_output),
        ) as attach_urls,
    ):
        result = await get_templates_usecase(
            templates_db=database,
            storage=storage,
        )
    get_metadata.assert_awaited_once_with(templates_db=database)
    attach_urls.assert_awaited_once_with(templates=templates, storage=storage)
    assert result is expected_output
