# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Tests for notify_project_submitted_usecase."""

from unittest.mock import AsyncMock
from unittest.mock import patch

import pytest

from recnavi.application.project.notify_project_submitted_usecase import (
    notify_project_submitted_usecase,
)


@pytest.mark.asyncio
async def test_notify_project_submitted_usecase_delegates_to_core():
    """Test usecase delegates to core and returns its output unchanged."""
    users_db = AsyncMock()
    notifier = AsyncMock()
    project = object()
    submitter = object()

    with patch(
        "recnavi.application.project.notify_project_submitted_usecase."
        "notify_project_submitted",
        new=AsyncMock(return_value=True),
    ) as mock_notify:
        result = await notify_project_submitted_usecase(
            users_db=users_db,
            notifier=notifier,
            project=project,
            submitter=submitter,
            base_url="http://localhost:5173",
        )

    mock_notify.assert_awaited_once_with(
        users_db=users_db,
        notifier=notifier,
        project=project,
        submitter=submitter,
        base_url="http://localhost:5173",
    )
    assert result is True
