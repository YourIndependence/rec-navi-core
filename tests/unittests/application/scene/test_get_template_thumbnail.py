# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Template thumbnail use-case delegation."""

from unittest.mock import AsyncMock
from unittest.mock import patch

import pytest

from recnavi.application.scene.get_template_thumbnail import (
    get_template_thumbnail_usecase,
)
from tests.mockups.mock_database import MockDatabase
from tests.mockups.mock_object_storage import MockObjectStorage


@pytest.mark.asyncio
async def test_thumbnail_usecase_delegates_to_core():
    database = MockDatabase()
    storage = MockObjectStorage(bucket_name="images")
    expected_output = (b"image", "image/jpeg")
    with patch(
        "recnavi.application.scene.get_template_thumbnail.get_template_thumbnail",
        new=AsyncMock(return_value=expected_output),
    ) as core:
        result = await get_template_thumbnail_usecase(
            templates_db=database,
            template_id="cafe",
            storage=storage,
        )
    assert result is expected_output
    core.assert_awaited_once_with(
        templates_db=database,
        template_id="cafe",
        storage=storage,
    )
