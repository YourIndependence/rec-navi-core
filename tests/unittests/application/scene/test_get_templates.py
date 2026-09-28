# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Tests for get_templates use case."""

from unittest.mock import AsyncMock
from unittest.mock import patch

import pytest

from recnavi.application.scene.get_templates import get_templates_usecase
from tests.mockups.mock_database import MockDatabase


@pytest.mark.asyncio
async def test_get_templates_usecase_delegates_to_core():
    """Test get_templates_usecase delegates and returns the core output."""
    templates_db = MockDatabase()
    expected_output = object()

    with patch(
        "recnavi.application.scene.get_templates.get_templates",
        new=AsyncMock(return_value=expected_output),
    ) as mock_get_templates:
        result = await get_templates_usecase(templates_db=templates_db)

    mock_get_templates.assert_awaited_with(templates_db=templates_db)
    assert result is expected_output
