# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or reproduction of this software is strictly prohibited.
#
# For internal use only.
# developer team.

"""Tests for update_template_usecase."""

from unittest.mock import AsyncMock
from unittest.mock import patch

import pytest

from recnavi.application.scene.update_template_usecase import (
    update_template_usecase,
)


@pytest.mark.asyncio
async def test_update_template_usecase_delegates_to_update_template():
    """Test usecase delegates to core update_template collaborator."""
    templates_db = AsyncMock()
    scenes_db = AsyncMock()
    storage = AsyncMock()
    expected_output = [object()]

    with patch(
        "recnavi.application.scene.update_template_usecase.update_template",
        new=AsyncMock(return_value=expected_output),
    ) as mock_update:
        result = await update_template_usecase(
            templates_db=templates_db,
            scenes_db=scenes_db,
            template_id="tpl",
            title="Title",
            scene_principals=["cooking"],
            thumbnail=None,
            bucket_name="test-bucket",
            storage=storage,
        )

    mock_update.assert_awaited_once_with(
        templates_db=templates_db,
        scenes_db=scenes_db,
        template_id="tpl",
        title="Title",
        scene_principals=["cooking"],
        thumbnail=None,
        bucket_name="test-bucket",
        storage=storage,
    )
    assert result is expected_output
