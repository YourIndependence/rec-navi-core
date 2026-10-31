# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or reproduction of this software is strictly prohibited.
#
# For internal use only.
# developer team.

"""Template application delegation."""

from unittest.mock import AsyncMock
from unittest.mock import patch

import pytest

from recnavi.application.scene.update_template import update_template_usecase
from tests.mockups.mock_users import get_mock_x_user


@pytest.mark.asyncio
async def test_update_template_delegates_and_signs():
    expected_output = AsyncMock()
    expected_output.attach_presigned_url.return_value = expected_output
    arguments = {
        "templates_db": AsyncMock(),
        "scenes_db": AsyncMock(),
        "storage": AsyncMock(),
        "user": get_mock_x_user(),
        "template_id": "tpl",
        "title": "Title",
        "scene_principals": [],
        "thumbnail_image": None,
    }
    with patch(
        "recnavi.application.scene.update_template.update_template",
        new=AsyncMock(return_value=expected_output),
    ) as collaborator:
        result = await update_template_usecase(**arguments)
    collaborator.assert_awaited_once_with(**arguments)
    expected_output.attach_presigned_url.assert_awaited_once_with(
        storage=arguments["storage"],
    )
    assert result is expected_output
